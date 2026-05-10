# app/mqtt/handlers.py
# MQTT 消息处理器
# 处理来自硬件设备的各类 MQTT 消息：握手、心跳、数据上报等

import json
import time
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import async_session_factory
from app.models.device import Device
from app.models.sensor_data import SensorData
from app.mqtt.client import mqtt_client
from app.mqtt.topics import get_status_topic, get_data_topic, get_control_topic
from app.websocket.manager import ws_manager


async def handle_mqtt_message(topic: str, payload: bytes) -> None:
    """
    MQTT 消息统一入口
    根据消息类型（type 字段）分发到不同的处理器

    支持的消息类型：
      - handshake: 设备握手
      - heartbeat: 设备心跳
      - data_report: 传感器数据上报
      - control_ack: 控制执行结果
    """
    try:
        data = json.loads(payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return  # 忽略格式错误的消息

    msg_type = data.get("type", "")
    device_id = data.get("device_id", "")

    # 根据消息类型分发处理
    handlers = {
        "handshake": _handle_handshake,
        "heartbeat": _handle_heartbeat,
        "data_report": _handle_data_report,
        "control_ack": _handle_control_ack,
    }

    handler = handlers.get(msg_type)
    if handler:
        await handler(device_id, data)


async def _handle_handshake(device_id: str, data: dict) -> None:
    """
    处理设备握手消息
    协议: MQTT 握手请求协议.json
    """
    async with async_session_factory() as db:
        from sqlalchemy import select
        result = await db.execute(select(Device).where(Device.device_id == device_id))
        device = result.scalar_one_or_none()

        if device is None:
            device = Device(
                device_id=device_id,
                chip_model=data.get("chip_model"),
                firmware_version=data.get("version"),
            )
            db.add(device)
        else:
            device.chip_model = data.get("chip_model")
            device.firmware_version = data.get("version")

        # 生成设备 Token
        import secrets
        device_token = f"dev_{secrets.token_hex(16)}"
        device.token = device_token
        device.status = "online"
        device.last_seen = datetime.now(timezone.utc)
        await db.commit()

    # 回复 handshake_ack（协议: 握手响应协议.json）
    ack_payload = json.dumps({
        "code": 200,
        "type": "handshake_ack",
        "msg": "握手成功",
        "timestamp": int(time.time()),
        "token": device_token,
        "expire_time": 86400,
    })
    await mqtt_client.publish(get_status_topic(device_id), ack_payload.encode())

    # 通过 WebSocket 通知前端设备上线
    await ws_manager.broadcast_device_status(device_id, "online")


async def _handle_heartbeat(device_id: str, data: dict) -> None:
    """
    处理设备心跳消息
    协议: 心跳包协议.json
    """
    async with async_session_factory() as db:
        from sqlalchemy import select
        result = await db.execute(select(Device).where(Device.device_id == device_id))
        device = result.scalar_one_or_none()

        if not device:
            return  # 设备未注册，忽略心跳

        # 验证 Token
        if device.token != data.get("token"):
            return

        device.status = "online"
        device.last_seen = datetime.now(timezone.utc)
        await db.commit()

    # 回复 heartbeat_ack
    ack_payload = json.dumps({
        "code": 200,
        "type": "heartbeat_ack",
        "msg": "ok",
        "timestamp": int(time.time()),
    })
    await mqtt_client.publish(get_status_topic(device_id), ack_payload.encode())

    # 广播设备心跳状态给前端（wifi / mqtt / screen / sensor 状态）
    heartbeat_status = data.get("status", {})
    if heartbeat_status:
        await ws_manager.broadcast_device_heartbeat(device_id, heartbeat_status)


async def _handle_data_report(device_id: str, data: dict) -> None:
    """
    处理传感器数据上报
    协议: 数据上报协议.json（结构: data.data.xxx, data.status.xxx）
    """
    # 协议嵌套结构: { data: { data: {...}, status: {...} } }
    payload = data.get("data", {})
    sensor_data = payload.get("data", {})
    status_data = payload.get("status", {})

    async with async_session_factory() as db:
        from sqlalchemy import select

        # 验证设备及 Token
        result = await db.execute(select(Device).where(Device.device_id == device_id))
        device = result.scalar_one_or_none()

        if not device or device.token != data.get("token"):
            ack_payload = json.dumps({
                "code": 401,
                "type": "data_report_ack",
                "msg": "Token无效",
                "timestamp": int(time.time()),
                "receive_status": False,
            })
            await mqtt_client.publish(get_data_topic(device_id), ack_payload.encode())
            return

        # 创建传感器数据记录
        record = SensorData(
            device_id=device_id,
            temperature=sensor_data.get("temperature"),
            humidity=sensor_data.get("humidity"),
            illuminance=sensor_data.get("illuminance"),
            aqi=sensor_data.get("aqi"),
            tvoc=sensor_data.get("tvoc"),
            eco2=sensor_data.get("eco2"),
            mold_risk=sensor_data.get("mold_risk"),
            gas=sensor_data.get("gas"),
            focus_mode=status_data.get("focus_mode", False),
            timestamp=datetime.fromtimestamp(data.get("timestamp", time.time()), tz=timezone.utc),
        )
        db.add(record)

        # 更新设备状态和固件版本
        device.status = "online"
        device.last_seen = datetime.now(timezone.utc)
        if sensor_data.get("version"):
            device.firmware_version = sensor_data.get("version")

        await db.commit()

    # 回复 data_report_ack（协议: 数据接收响应协议.json）
    ack_payload = json.dumps({
        "code": 200,
        "type": "data_report_ack",
        "msg": "gogogookkk",
        "timestamp": int(time.time()),
        "receive_status": True,
    })
    await mqtt_client.publish(get_data_topic(device_id), ack_payload.encode())

    # 通过 WebSocket 推送传感器数据给前端
    await ws_manager.broadcast_sensor_data(device_id, sensor_data)


async def _handle_control_ack(device_id: str, data: dict) -> None:
    """
    处理控制执行结果通知
    通过 WebSocket 推送执行结果给前端
    """
    command = data.get("command", "")
    result_status = data.get("result", "")
    value = data.get("value", "")

    # 通过 WebSocket 推送给前端
    await ws_manager.broadcast_control_result(device_id, command, value, result_status)
