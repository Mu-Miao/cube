from collections import defaultdict
import json
import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.device import Device
from app.models.sensor_data import SensorData
from app.models.user import User
from app.schemas.base import ApiResponse
from app.services import llm_service

router = APIRouter(prefix="/ai", tags=["AI 分析"])

LLM_ERROR_CODE = 5001


def _extract_json_object(text: str) -> dict | None:
    """Extract a JSON object from plain or markdown-fenced LLM output."""
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fenced:
        cleaned = fenced.group(1)
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            cleaned = cleaned[start:end + 1]

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _sensor_snapshot(record: SensorData | None) -> dict:
    if record is None:
        return {"status": "no_data"}

    return {
        "temperature": record.temperature,
        "humidity": record.humidity,
        "illuminance": record.illuminance,
        "aqi": record.aqi,
        "pm25": record.pm25,
        "tvoc": record.tvoc,
        "eco2": record.eco2,
        "mold_risk": record.mold_risk,
        "gas": record.gas,
        "wifi_rssi": record.wifi_rssi,
        "timestamp": record.timestamp.isoformat() if record.timestamp else None,
    }


def _normalize_llm_suggestions(parsed: dict) -> dict | None:
    raw_items = parsed.get("suggestions")
    if not isinstance(raw_items, list):
        return None

    icon_aliases = {
        "co2": "eco2",
        "carbon": "eco2",
        "wifi": "i",
        "wifi_rssi": "i",
    }
    allowed_icons = {"i", "light", "wind", "water", "temp", "aqi", "tvoc", "eco2", "mold", "gas", "ok"}
    suggestions = []
    for item in raw_items[:5]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        desc = str(item.get("desc") or item.get("description") or "").strip()
        icon = str(item.get("icon") or "i").strip().lower()
        icon = icon.split("|", 1)[0]
        icon = icon_aliases.get(icon, icon)
        if icon not in allowed_icons:
            icon = "i"
        if title and desc:
            suggestions.append({"icon": icon, "title": title, "desc": desc})

    if not suggestions:
        return None

    return {
        "suggestions": suggestions,
        "source": "llm",
    }


def _normalize_llm_weekly_report(parsed: dict, fallback_days: list[dict]) -> dict | None:
    summary = str(parsed.get("summary") or "").strip()
    raw_days = parsed.get("days")
    days = fallback_days

    if isinstance(raw_days, list):
        normalized_days = []
        for item in raw_days[:7]:
            if not isinstance(item, dict):
                continue
            date = str(item.get("date") or "").strip()
            if not date:
                continue
            normalized_days.append({
                "date": date,
                "temperature": item.get("temperature"),
                "humidity": item.get("humidity"),
                "aqi": item.get("aqi"),
                "sample_count": item.get("sample_count") or 0,
            })
        if normalized_days:
            days = normalized_days

    if not summary:
        return None

    return {
        "days": days,
        "summary": summary,
        "source": "llm",
    }


async def _ask_llm_json(prompt: str) -> dict | None:
    result = await llm_service.chat_api(
        prompt,
        system=(
            "你是智能桌面魔方的环境分析助手。"
            "必须只返回合法 JSON，不要 Markdown，不要解释，不要额外文本。"
            "如果任务是生成建议，返回示例："
            '{"suggestions":[{"icon":"wind","title":"空气流通不足","desc":"建议开窗通风 10-15 分钟。"}]}。'
            "如果任务是生成周报，返回示例："
            '{"summary":"本周环境整体稳定，建议继续保持定时通风。",'
            '"days":[{"date":"2026-07-12","temperature":25.1,"humidity":48.2,"aqi":38,"sample_count":42}]}。'
            "字段名必须和示例完全一致。"
        ),
    )
    if not result:
        return None
    return _extract_json_object(result)


async def _verify_device_ownership(device_id: str, user_id: int, db: AsyncSession):
    result = await db.execute(
        select(Device).where(
            Device.device_id == device_id,
            Device.bound_user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def _get_latest_sensor_data(device_id: str, db: AsyncSession):
    result = await db.execute(
        select(SensorData)
        .where(SensorData.device_id == device_id)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _range_score(value: float | None, ideal_min: float, ideal_max: float, hard_min: float, hard_max: float) -> int:
    if value is None:
        return 70
    if ideal_min <= value <= ideal_max:
        return 100
    if value < ideal_min:
        return max(0, round(100 * (value - hard_min) / (ideal_min - hard_min)))
    return max(0, round(100 * (hard_max - value) / (hard_max - ideal_max)))


def _lower_is_better_score(value: float | None, good: float, poor: float) -> int:
    if value is None:
        return 70
    if value <= good:
        return 100
    if value >= poor:
        return 0
    return round(100 * (poor - value) / (poor - good))


def _build_score(record: SensorData | None):
    if record is None:
        return {
            "score": 0,
            "level": "no_data",
            "breakdown": {
                "temperature": 0,
                "humidity": 0,
                "air_quality": 0,
                "comfort": 0,
            },
            "summary": "暂无传感器数据，请先连接设备并上报数据。",
        }

    temperature = _range_score(record.temperature, 22, 27, 10, 38)
    humidity = _range_score(record.humidity, 40, 65, 15, 90)
    aqi = _lower_is_better_score(record.aqi, 50, 150)
    eco2 = _lower_is_better_score(record.eco2, 800, 2000)
    tvoc = _lower_is_better_score(record.tvoc, 200, 1000)
    gas = 100 if (record.gas or 0) <= 0 else 0
    mold = _lower_is_better_score(record.mold_risk, 1, 3)
    air_quality = round((aqi * 0.35) + (eco2 * 0.25) + (tvoc * 0.2) + (gas * 0.2))
    comfort = round((temperature * 0.45) + (humidity * 0.35) + (mold * 0.2))
    score = round((temperature * 0.2) + (humidity * 0.15) + (air_quality * 0.4) + (comfort * 0.25))

    if score >= 90:
        level = "excellent"
        summary = "当前室内环境整体优秀，各项指标均处于舒适范围。"
    elif score >= 70:
        level = "good"
        summary = "当前室内环境整体良好，适合工作与休息。"
    elif score >= 40:
        level = "fair"
        summary = "当前室内环境一般，建议关注空气质量或湿度变化。"
    else:
        level = "poor"
        summary = "当前室内环境较差，请尽快通风、除湿或检查安全风险。"

    return {
        "score": score,
        "level": level,
        "breakdown": {
            "temperature": temperature,
            "humidity": humidity,
            "air_quality": air_quality,
            "comfort": comfort,
        },
        "summary": summary,
    }


def _build_risks(record: SensorData | None):
    if record is None:
        return {"risks": [], "highest_level": "none"}

    risks = []

    def add(field: str, level: str, title: str, message: str):
        risks.append({
            "field": field,
            "level": level,
            "title": title,
            "message": message,
        })

    if (record.gas or 0) > 0:
        add("gas", "critical", "燃气安全异常", "检测到燃气风险，请立即开窗通风并检查气源。")
    if (record.mold_risk or 0) >= 3:
        add("mold_risk", "critical", "霉菌风险极高", "湿度或环境条件已达到高风险，请尽快除湿并检查墙角/织物。")
    elif (record.mold_risk or 0) >= 2:
        add("mold_risk", "warning", "霉菌风险偏高", "建议降低湿度，保持空气流通。")
    if (record.eco2 or 0) >= 1500:
        add("eco2", "critical", "CO2 浓度过高", "建议立即开窗通风，避免长时间停留。")
    elif (record.eco2 or 0) >= 1000:
        add("eco2", "warning", "CO2 浓度偏高", "建议通风 10-15 分钟。")
    if (record.tvoc or 0) >= 1000:
        add("tvoc", "critical", "TVOC 严重超标", "建议立即通风，并排查异味或装修污染来源。")
    elif (record.tvoc or 0) >= 500:
        add("tvoc", "warning", "TVOC 偏高", "建议打开窗户或空气净化设备。")

    level_rank = {"none": 0, "warning": 1, "critical": 2}
    highest = "none"
    for risk in risks:
        if level_rank[risk["level"]] > level_rank[highest]:
            highest = risk["level"]

    return {"risks": risks, "highest_level": highest}


def _build_suggestions(record: SensorData | None):
    if record is None:
        return {
            "suggestions": [
                {"icon": "i", "title": "暂无实时数据", "desc": "请先连接设备并等待一次传感器上报。"},
            ]
        }

    suggestions = []
    if record.illuminance is not None and record.illuminance < 300:
        suggestions.append({"icon": "light", "title": "光照偏低", "desc": "建议打开主灯或拉开窗帘。"})
    if record.eco2 is not None and record.eco2 >= 1000:
        suggestions.append({"icon": "wind", "title": "空气流通不足", "desc": "建议开窗通风 10-15 分钟。"})
    if record.humidity is not None and record.humidity > 65:
        suggestions.append({"icon": "water", "title": "湿度偏高", "desc": "建议开启除湿或加强通风。"})
    if record.humidity is not None and record.humidity < 35:
        suggestions.append({"icon": "water", "title": "湿度偏低", "desc": "建议适当加湿，避免长时间干燥。"})
    if record.temperature is not None and record.temperature > 28:
        suggestions.append({"icon": "temp", "title": "温度偏高", "desc": "建议降低空调温度或加强空气循环。"})
    if record.temperature is not None and record.temperature < 18:
        suggestions.append({"icon": "temp", "title": "温度偏低", "desc": "建议适当升温，保持桌面工作舒适度。"})
    if not suggestions:
        suggestions.append({"icon": "ok", "title": "环境状态良好", "desc": "当前环境指标比较稳定，继续保持。"})

    return {"suggestions": suggestions, "source": "rule"}


def _build_weekly_days(records: list[SensorData]) -> list[dict]:
    grouped = defaultdict(list)
    for record in records:
        grouped[record.timestamp.date().isoformat()].append(record)

    days = []
    for day, items in sorted(grouped.items()):
        def avg(field: str):
            values = [getattr(item, field) for item in items if getattr(item, field) is not None]
            return round(sum(values) / len(values), 1) if values else None

        days.append({
            "date": day,
            "temperature": avg("temperature"),
            "humidity": avg("humidity"),
            "aqi": avg("aqi"),
            "sample_count": len(items),
        })
    return days


@router.get("/{device_id}/score", response_model=ApiResponse)
async def get_environment_score(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """环境综合评分（0-100）"""
    device = await _verify_device_ownership(device_id, current_user.id, db)
    if not device:
        return ApiResponse(code=3002, message="设备未绑定", data=None)

    record = await _get_latest_sensor_data(device_id, db)
    return ApiResponse(data=_build_score(record))


@router.get("/{device_id}/risks", response_model=ApiResponse)
async def get_risk_warnings(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """风险预警列表"""
    device = await _verify_device_ownership(device_id, current_user.id, db)
    if not device:
        return ApiResponse(code=3002, message="设备未绑定", data=None)

    record = await _get_latest_sensor_data(device_id, db)
    return ApiResponse(data=_build_risks(record))


@router.get("/{device_id}/suggestions", response_model=ApiResponse)
async def get_ai_suggestions(
    device_id: str,
    force_llm: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 建议"""
    device = await _verify_device_ownership(device_id, current_user.id, db)
    if not device:
        return ApiResponse(code=3002, message="设备未绑定", data=None)

    record = await _get_latest_sensor_data(device_id, db)
    rule_data = _build_suggestions(record)
    if not force_llm:
        return ApiResponse(data=rule_data)

    prompt = (
        "请基于以下智能桌面魔方传感器数据生成 3-5 条具体环境优化建议。"
        "返回 JSON 格式："
        '{"suggestions":[{"icon":"wind|water|temp|light|aqi|tvoc|eco2|mold|gas|ok",'
        '"title":"短标题","desc":"一句可执行建议"}]}。'
        f"\n设备ID：{device_id}"
        f"\n传感器数据：{json.dumps(_sensor_snapshot(record), ensure_ascii=False)}"
        f"\n规则引擎参考：{json.dumps(rule_data, ensure_ascii=False)}"
    )
    parsed = await _ask_llm_json(prompt)
    llm_data = _normalize_llm_suggestions(parsed or {})
    if not llm_data:
        return ApiResponse(
            code=LLM_ERROR_CODE,
            message="LLM 未返回有效建议结果，请确认后端已配置和小眠对话相同的 LLM_API_KEY / LLM_API_BASE_URL / LLM_API_MODEL。",
            data=rule_data,
        )

    return ApiResponse(data=llm_data)


@router.get("/{device_id}/weekly-report", response_model=ApiResponse)
async def get_weekly_report(
    device_id: str,
    force_llm: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """周报数据"""
    device = await _verify_device_ownership(device_id, current_user.id, db)
    if not device:
        return ApiResponse(code=3002, message="设备未绑定", data=None)

    result = await db.execute(
        select(SensorData)
        .where(SensorData.device_id == device_id)
        .order_by(SensorData.timestamp.desc())
        .limit(7 * 24 * 60)
    )
    records = list(reversed(result.scalars().all()))

    days = _build_weekly_days(records)
    rule_data = {"days": days, "summary": "", "source": "rule"}
    if not force_llm:
        return ApiResponse(data=rule_data)

    prompt = (
        "请基于最近 7 天环境数据生成智能桌面魔方周报摘要。"
        "返回 JSON 格式："
        '{"summary":"80字以内中文总结，包含趋势和建议","days":[{"date":"YYYY-MM-DD",'
        '"temperature":数字或null,"humidity":数字或null,"aqi":数字或null,"sample_count":数字}]}。'
        "days 可以直接沿用输入数据。"
        f"\n设备ID：{device_id}"
        f"\n最近7天聚合数据：{json.dumps(days, ensure_ascii=False)}"
    )
    parsed = await _ask_llm_json(prompt)
    llm_data = _normalize_llm_weekly_report(parsed or {}, days)
    if not llm_data:
        return ApiResponse(
            code=LLM_ERROR_CODE,
            message="LLM 未返回有效周报结果，请确认后端已配置和小眠对话相同的 LLM_API_KEY / LLM_API_BASE_URL / LLM_API_MODEL。",
            data=rule_data,
        )

    return ApiResponse(data=llm_data)
