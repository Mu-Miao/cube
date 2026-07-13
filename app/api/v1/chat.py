# app/api/v1/chat.py
# 小眠 AI 对话端点
# POST /api/v1/chat/stream — SSE 流式输出
# 自动注入用户设备的实时传感器数据，让 AI 能回答真实环境问题

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.device import Device
from app.models.sensor_data import SensorData
from app.models.user import User
from app.services import llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["小眠对话"])

# 小眠系统人设提示词
SYSTEM_PROMPT = """你是「小眠」，智能桌面魔方的 AI 小助手。你的性格温暖、活泼、有点可爱。

关于你：
- 你是桌面魔方设备上的智能助手，帮助用户管理和了解他们的设备与环境。
- 你可以回答关于设备状态、传感器数据（温度、湿度、AQI、TVOC、eCO2 等）、控制指令、AI 分析等方面的问题。
- 你的语气应该友好可爱，偶尔使用一些表情符号，但不要过度。
- 回答要简洁实用，不要太长。
- 如果用户问的问题与桌面魔方无关，你也可以友好地回答，但会自然地引导回设备和环境话题。
- 你可以给出关于改善室内环境的建议，比如通风、调温、开灯等。
- 你始终用中文回答。
- 当用户问到环境相关的问题时，请参考下面提供的实时设备数据来回答，给出具体数值和建议。"""


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    device_id: Optional[str] = None  # 可选：指定当前设备，为空则自动选第一个在线设备


# 传感器字段的中文映射和阈值
SENSOR_LABELS = {
    "temperature": ("温度", "℃", 28, 30),
    "humidity": ("湿度", "%RH", 70, 80),
    "aqi": ("空气质量指数", "", 100, 150),
    "tvoc": ("TVOC", "ppb", 200, 300),
    "eco2": ("eCO2", "ppm", 800, 1000),
    "illuminance": ("光照强度", "lx", None, None),
    "gas": ("燃气浓度", "", 0.5, 1.0),
    "mold_risk": ("霉菌风险", "", None, None),
    "wifi_rssi": ("WiFi信号", "dBm", None, None),
}

MOLD_RISK_MAP = {0: "无风险", 1: "低风险", 2: "中风险", 3: "高风险"}


def _format_sensor_value(value, label, unit, warn_thresh, crit_thresh):
    """格式化单个传感器值为自然语言"""
    if value is None:
        return None

    if label == "霉菌风险":
        return MOLD_RISK_MAP.get(int(value), "未知")
    if label == "燃气浓度":
        return "正常" if value <= 0 else f"{value}（异常！）"

    text = f"{value}{unit}"
    if crit_thresh is not None and value >= crit_thresh:
        text += "（危险！）"
    elif warn_thresh is not None and value >= warn_thresh:
        text += "（偏高）"
    return text


async def _build_device_context(user_id: int, device_id: Optional[str], db: AsyncSession) -> str:
    """
    查询用户的设备数据和传感器数据，生成注入到 system prompt 的上下文文本。
    如果没有设备或数据，返回空字符串。
    """
    # 1. 获取目标设备
    device: Optional[Device] = None
    if device_id:
        result = await db.execute(
            select(Device).where(
                Device.device_id == device_id,
                Device.bound_user_id == user_id,
            )
        )
        device = result.scalar_one_or_none()

    if not device:
        # 自动选第一个在线设备
        result = await db.execute(
            select(Device)
            .where(Device.bound_user_id == user_id, Device.status == "online")
            .limit(1)
        )
        device = result.scalar_one_or_none()

    if not device:
        # 退而求其次：任意一个设备
        result = await db.execute(
            select(Device).where(Device.bound_user_id == user_id).limit(1)
        )
        device = result.scalar_one_or_none()

    if not device:
        return "\n\n当前用户尚未绑定任何设备，无法查看传感器数据。请引导用户先去绑定设备。"

    # 2. 获取最新传感器数据
    result = await db.execute(
        select(SensorData)
        .where(SensorData.device_id == device.device_id)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    sensor: Optional[SensorData] = result.scalar_one_or_none()

    # 3. 构建上下文文本
    lines = [
        f"\n\n【当前设备实时数据】",
        f"设备名称：{device.device_name}",
        f"设备ID：{device.device_id}",
        f"设备状态：{'在线' if device.status == 'online' else '离线'}",
    ]

    if device.chip_model:
        lines.append(f"芯片型号：{device.chip_model}")
    if device.firmware_version:
        lines.append(f"固件版本：{device.firmware_version}")
    if device.last_seen:
        lines.append(f"最后在线：{device.last_seen.strftime('%Y-%m-%d %H:%M:%S')}")

    if sensor:
        lines.append(f"数据时间：{sensor.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("传感器读数：")

        for field, (label, unit, warn, crit) in SENSOR_LABELS.items():
            value = getattr(sensor, field, None)
            if value is not None:
                formatted = _format_sensor_value(value, label, unit, warn, crit)
                if formatted:
                    lines.append(f"  - {label}: {formatted}")
    else:
        lines.append("（暂无传感器数据，设备可能刚绑定或尚未上报数据）")

    return "\n".join(lines)


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    小眠 AI 流式对话
    前端发送对话历史 + 可选的 device_id，后端自动查询设备实时数据注入到系统提示词中，
    然后调用 LLM，以 SSE 格式逐块返回文本。
    """
    # 1. 查询设备数据上下文
    device_context = await _build_device_context(current_user.id, req.device_id, db)

    # 2. 拼接完整消息列表：系统提示词 + 设备上下文 + 对话历史
    system_content = SYSTEM_PROMPT + device_context
    full_messages = [{"role": "system", "content": system_content}]
    for msg in req.messages:
        full_messages.append({"role": msg.role, "content": msg.content})

    async def event_generator():
        async for chunk in llm_service.chat_stream(full_messages):
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
