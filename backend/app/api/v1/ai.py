import json
import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_owned_device
from app.db.session import get_db
from app.models.device import Device
from app.models.sensor_data import SensorData
from app.schemas.base import ApiResponse
from app.utils.timezone import shanghai_isoformat
from app.services import llm_service
from app.services.ai_risk_service import build_risks
from app.services.ai_score_service import build_score
from app.services.ai_suggestion_service import build_suggestions
from app.services.weekly_report_service import aggregate_weekly_days

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
        "timestamp": shanghai_isoformat(record.timestamp),
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


async def _get_latest_sensor_data(device_id: str, db: AsyncSession):
    result = await db.execute(
        select(SensorData)
        .where(SensorData.device_id == device_id)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.get("/{device_id}/score", response_model=ApiResponse)
async def get_environment_score(
    device_id: str,
    _device: Device = Depends(require_owned_device),
    db: AsyncSession = Depends(get_db),
):
    """环境综合评分（0-100）"""
    record = await _get_latest_sensor_data(device_id, db)
    return ApiResponse(data=build_score(record))


@router.get("/{device_id}/risks", response_model=ApiResponse)
async def get_risk_warnings(
    device_id: str,
    _device: Device = Depends(require_owned_device),
    db: AsyncSession = Depends(get_db),
):
    """风险预警列表"""
    record = await _get_latest_sensor_data(device_id, db)
    return ApiResponse(data=build_risks(record))


@router.get("/{device_id}/suggestions", response_model=ApiResponse)
async def get_ai_suggestions(
    device_id: str,
    force_llm: bool = Query(False),
    _device: Device = Depends(require_owned_device),
    db: AsyncSession = Depends(get_db),
):
    """AI 建议"""
    record = await _get_latest_sensor_data(device_id, db)
    rule_data = build_suggestions(record)
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
    _device: Device = Depends(require_owned_device),
    db: AsyncSession = Depends(get_db),
):
    """周报数据"""
    days = await aggregate_weekly_days(db, device_id)
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
