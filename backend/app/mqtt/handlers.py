# app/mqtt/handlers.py
# MQTT 消息处理器
# 处理来自硬件设备的各类 MQTT 消息：握手、心跳、数据上报等

import json
import re
import time
from datetime import datetime, timezone

from loguru import logger
from pydantic import ValidationError
from sqlalchemy import select

from app.config import settings
from app.db.session import async_session_factory
from app.models.device import Device
from app.models.ota_log import OtaLog
from app.models.sensor_data import SensorData
from app.mqtt.client import mqtt_client
from app.mqtt.topics import get_status_topic, get_data_topic
from app.schemas.data import SensorDataPayload
from app.services.alert_service import check_alerts
from app.services.control_status import normalize_control_status, persist_latest_control_status
from app.services.control_queue import control_queue
from app.services.device_credentials import (
    authorize_handshake,
    issue_device_token,
    verify_device_token,
)
from app.services.firmware_service import (
    FIRMWARE_DIR,
    build_signed_firmware_url,
    firmware_md5,
)
from app.utils.timezone import shanghai_isoformat
from app.websocket.manager import ws_manager


def _normalize_pm25_key(sensor_data: dict) -> dict:
    normalized = sensor_data.copy()
    if normalized.get("pm25") is None:
        for key in ("pm2_5", "pm2.5", "PM2.5", "pm25_estimated"):
            if normalized.get(key) is not None:
                normalized["pm25"] = normalized[key]
                break
    return normalized


async def handle_mqtt_message(topic: str, payload: bytes) -> None:
    """
    MQTT 消息统一入口
    根据消息类型（type 字段）分发到不同的处理器

    支持的消息类型：
      - handshake: 设备握手
      - heartbeat: 设备心跳
      - data_report: 传感器数据上报
      - version_check: 设备请求检查固件版本
      - control_ack: 控制执行结果
    """
    try:
        data = json.loads(payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.warning("忽略无效 MQTT 消息: topic={}", topic)
        return  # 忽略格式错误的消息

    msg_type = data.get("type", "")
    device_id = data.get("device_id", "")
    logger.info("收到 MQTT 消息: topic={}, type={}, device_id={}", topic, msg_type, device_id)

    # 根据消息类型分发处理
    handlers = {
        "handshake": _handle_handshake,
        "heartbeat": _handle_heartbeat,
        "data_report": _handle_data_report,
        "version_check": _handle_version_check,
        "control_ack": _handle_control_ack,
    }

    handler = handlers.get(msg_type)
    if handler:
        await handler(device_id, data)
    else:
        logger.warning("未处理的 MQTT 消息类型: type={}, device_id={}", msg_type, device_id)


async def _handle_handshake(device_id: str, data: dict) -> None:
    """
    处理设备握手消息
    协议: MQTT 握手请求协议.json
    """
    async with async_session_factory() as db:
        result = await db.execute(select(Device).where(Device.device_id == device_id))
        device = result.scalar_one_or_none()
        if not await authorize_handshake(
            db,
            device,
            device_id,
            data.get("pairing_code"),
            data.get("token"),
        ):
            ack_payload = json.dumps({
                "code": 403,
                "type": "handshake_ack",
                "msg": "配对凭证无效",
                "timestamp": int(time.time()),
                "token": "",
                "expire_time": 0,
            })
            await mqtt_client.publish(get_status_topic(device_id), ack_payload.encode())
            return

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

        device_token = issue_device_token(device)
        device.status = "online"
        device.last_seen = datetime.now(timezone.utc)
        await db.commit()
        logger.info(
            "设备握手成功: device_id={}, chip_model={}, version={}",
            device_id,
            data.get("chip_model"),
            data.get("version"),
        )

    # 回复 handshake_ack（协议: 握手响应协议.json）
    ack_payload = json.dumps({
        "code": 200,
        "type": "handshake_ack",
        "msg": "握手成功",
        "timestamp": int(time.time()),
        "token": device_token,
        "expire_time": settings.DEVICE_TOKEN_EXPIRE_SECONDS,
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
        result = await db.execute(select(Device).where(Device.device_id == device_id))
        device = result.scalar_one_or_none()

        if not device:
            logger.warning("心跳忽略: 设备未注册 device_id={}", device_id)
            return  # 设备未注册，忽略心跳

        # 验证 Token
        if not verify_device_token(device, data.get("token")):
            logger.warning("心跳 Token 无效: device_id={}", device_id)
            return

        device.status = "online"
        device.last_seen = datetime.now(timezone.utc)
        heartbeat_status = await persist_latest_control_status(
            db,
            device_id,
            data.get("status"),
        )
        await db.commit()
        logger.info("设备心跳成功: device_id={}", device_id)

    # 回复 heartbeat_ack
    ack_payload = json.dumps({
        "code": 200,
        "type": "heartbeat_ack",
        "msg": "ok",
        "timestamp": int(time.time()),
    })
    await mqtt_client.publish(get_status_topic(device_id), ack_payload.encode())

    # 广播设备心跳状态给前端（wifi / mqtt / screen / sensor 状态）
    if heartbeat_status:
        await ws_manager.broadcast_device_heartbeat(device_id, heartbeat_status)


async def _handle_data_report(device_id: str, data: dict) -> None:
    """
    处理传感器数据上报
    协议: 数据上报协议.json（结构: data.data.xxx, data.status.xxx）
    """
    # 支持两种结构:
    # 1. 硬件 MQTT: { data: { data: {...}, status: {...} } }
    # 2. 扁平格式: { data: {...}, status: {...} }
    payload = data.get("data", {})
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        sensor_data = payload.get("data", {})
        status_data = payload.get("status", {})
    else:
        sensor_data = payload if isinstance(payload, dict) else {}
        status_data = data.get("status", {})
    sensor_data = _normalize_pm25_key(sensor_data)
    try:
        sensor_data = SensorDataPayload.model_validate(sensor_data).model_dump()
    except ValidationError:
        logger.warning("数据上报范围校验失败: device_id={}", device_id)
        ack_payload = json.dumps({
            "code": 422,
            "type": "data_report_ack",
            "msg": "传感器数据超出允许范围",
            "timestamp": int(time.time()),
            "receive_status": False,
        })
        await mqtt_client.publish(get_data_topic(device_id), ack_payload.encode())
        return

    async with async_session_factory() as db:
        # 验证设备及 Token
        result = await db.execute(select(Device).where(Device.device_id == device_id))
        device = result.scalar_one_or_none()

        if not device:
            logger.warning("数据上报失败: 设备未注册 device_id={}", device_id)
            ack_payload = json.dumps({
                "code": 404,
                "type": "data_report_ack",
                "msg": "设备未注册",
                "timestamp": int(time.time()),
                "receive_status": False,
            })
            await mqtt_client.publish(get_data_topic(device_id), ack_payload.encode())
            return

        if not verify_device_token(device, data.get("token")):
            logger.warning("数据上报 Token 无效: device_id={}", device_id)
            ack_payload = json.dumps({
                "code": 401,
                "type": "data_report_ack",
                "msg": "Token无效",
                "timestamp": int(time.time()),
                "receive_status": False,
            })
            await mqtt_client.publish(get_data_topic(device_id), ack_payload.encode())
            return

        control_status = normalize_control_status(status_data)

        # 创建传感器数据记录
        record = SensorData(
            device_id=device_id,
            temperature=sensor_data.get("temperature"),
            humidity=sensor_data.get("humidity"),
            illuminance=sensor_data.get("illuminance"),
            aqi=sensor_data.get("aqi"),
            pm25=sensor_data.get("pm25"),
            tvoc=sensor_data.get("tvoc"),
            eco2=sensor_data.get("eco2"),
            mold_risk=sensor_data.get("mold_risk"),
            gas=sensor_data.get("gas"),
            wifi_rssi=sensor_data.get("wifi_rssi"),
            focus_mode=control_status.get("focus_mode"),
            light=control_status.get("light"),
            light_brightness=control_status.get("light_brightness"),
            color_temperature=control_status.get("color_temperature"),
            wechat_notify=control_status.get("wechat_notify"),
            auto_screen_brightness=control_status.get("auto_screen_brightness"),
            screen_brightness=control_status.get("screen_brightness"),
            timestamp=datetime.fromtimestamp(data.get("timestamp", time.time()), tz=timezone.utc),
        )
        db.add(record)

        # 在线状态只由握手/心跳维护，避免传感器数据把失联设备顶成在线。
        if sensor_data.get("version"):
            device.firmware_version = sensor_data.get("version")

        await db.commit()
        logger.info(
            "数据上报成功: device_id={}, temp={}, hum={}, aqi={}, eco2={}",
            device_id,
            sensor_data.get("temperature"),
            sensor_data.get("humidity"),
            sensor_data.get("aqi"),
            sensor_data.get("eco2"),
        )

    # 数据库提交后立即推送给前端，不等待 MQTT ACK 的网络往返。
    await ws_manager.broadcast_sensor_data(device_id, {
        **sensor_data,
        **control_status,
        "timestamp": shanghai_isoformat(record.timestamp),
    })

    # 回复 data_report_ack（协议: 数据接收响应协议.json）
    ack_payload = json.dumps({
        "code": 200,
        "type": "data_report_ack",
        "msg": "数据接收成功",
        "timestamp": int(time.time()),
        "receive_status": True,
    })
    await mqtt_client.publish(get_data_topic(device_id), ack_payload.encode())

    await check_alerts(device_id, {
        "gas": sensor_data.get("gas"),
        "tvoc": sensor_data.get("tvoc"),
        "eco2": sensor_data.get("eco2"),
        "mold_risk": sensor_data.get("mold_risk"),
    })


def _parse_version(value: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", value or "")
    return tuple(int(part) for part in parts)


def _latest_firmware() -> tuple[str, str, str] | None:
    candidates = []
    for path in FIRMWARE_DIR.glob("*.bin"):
        version_match = re.search(r"v?(\d+(?:\.\d+)+)", path.name)
        if not version_match:
            continue
        version = version_match.group(1)
        candidates.append((_parse_version(version), version, path))
    if not candidates:
        return None

    _version_key, version, path = max(candidates, key=lambda item: item[0])
    md5 = firmware_md5(path)
    base_url = settings.FIRMWARE_PUBLIC_BASE_URL.strip()
    if not base_url:
        logger.warning("无法生成 OTA URL: FIRMWARE_PUBLIC_BASE_URL 未配置")
        return None
    return version, build_signed_firmware_url(base_url, path.name), md5


async def _handle_version_check(device_id: str, data: dict) -> None:
    """
    处理设备版本检查请求。
    协议: 版本检查请求协议.json -> OTA更新推送协议(1).json
    """
    async with async_session_factory() as db:
        result = await db.execute(select(Device).where(Device.device_id == device_id))
        device = result.scalar_one_or_none()

        if not device:
            logger.warning("版本检查失败: 设备未注册 device_id={}", device_id)
            payload = {
                "code": 403,
                "type": "ota_update",
                "msg": "设备未授权",
                "timestamp": int(time.time()),
                "url": "",
                "version": data.get("current_version", ""),
                "md5": "",
            }
            await mqtt_client.publish(get_status_topic(device_id), json.dumps(payload).encode())
            return

        if not verify_device_token(device, data.get("token")):
            logger.warning("版本检查 Token 无效: device_id={}", device_id)
            payload = {
                "code": 401,
                "type": "ota_update",
                "msg": "Token无效",
                "timestamp": int(time.time()),
                "url": "",
                "version": data.get("current_version", ""),
                "md5": "",
            }
            await mqtt_client.publish(get_status_topic(device_id), json.dumps(payload).encode())
            return

        device.status = "online"
        device.last_seen = datetime.now(timezone.utc)
        if data.get("current_version"):
            device.firmware_version = data.get("current_version")
        await db.commit()

    latest = _latest_firmware()
    current_version = data.get("current_version", "")
    if latest and _parse_version(latest[0]) > _parse_version(current_version):
        target_version, firmware_url, firmware_md5 = latest
        payload = {
            "code": 200,
            "type": "ota_update",
            "msg": "新版本可用",
            "timestamp": int(time.time()),
            "url": firmware_url,
            "version": target_version,
            "md5": firmware_md5,
        }
    else:
        payload = {
            "code": 204,
            "type": "ota_update",
            "msg": "已是最新版本",
            "timestamp": int(time.time()),
            "url": "",
            "version": current_version,
            "md5": "",
        }

    await mqtt_client.publish(
        get_status_topic(device_id),
        json.dumps(payload, ensure_ascii=False).encode(),
    )
    logger.info(
        "版本检查响应: device_id={}, current_version={}, code={}",
        device_id,
        current_version,
        payload["code"],
    )


async def _handle_control_ack(device_id: str, data: dict) -> None:
    """
    处理控制执行结果通知
    通过 WebSocket 推送执行结果给前端
    """
    command = data.get("command", "")
    result_status = data.get("result", "")
    value = data.get("value", "")
    async with async_session_factory() as db:
        device = (
            await db.execute(select(Device).where(Device.device_id == device_id))
        ).scalar_one_or_none()
        if not verify_device_token(device, data.get("token")):
            logger.warning("忽略无效控制 ACK: device_id={}", device_id)
            return

        logger.info(
            "控制结果 ACK: device_id={}, command={}, value={}, result={}",
            device_id,
            command,
            value,
            result_status,
        )

        if command == "ota_update":
            query = select(OtaLog).where(
                OtaLog.device_id == device_id,
                OtaLog.status == "pushed",
            )
            if value:
                query = query.where(OtaLog.target_version == str(value))
            query = query.order_by(OtaLog.id.desc()).limit(1)
            ota_log = (await db.execute(query)).scalar_one_or_none()
            if ota_log:
                ota_log.status = "success" if str(result_status).lower() in {"success", "ok"} else "failed"
                ota_log.remark = str(data.get("message") or "")
                await db.commit()
                logger.info(
                    "OTA 日志已更新: device_id={}, version={}, status={}",
                    device_id,
                    ota_log.target_version,
                    ota_log.status,
                )
            else:
                logger.warning(
                    "未找到对应的 OTA 推送日志: device_id={}, version={}",
                    device_id,
                    value,
                )
        else:
            await db.commit()

    command_id = str(data.get("command_id") or "")
    if command_id:
        await control_queue.acknowledge(device_id, command_id)

    # 通过 WebSocket 推送给前端
    await ws_manager.broadcast_control_result(device_id, command, value, result_status)
