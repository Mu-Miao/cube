# app/api/v1/control.py
# 远程控制接口
# 提供：用户下发控制指令、设备拉取指令、执行结果通知

import json
import time
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_owned_device
from app.db.session import get_db
from app.models.device import Device
from app.models.operation_log import OperationLog
from app.mqtt.client import mqtt_client
from app.mqtt.topics import get_control_topic
from app.schemas.base import ApiResponse
from app.services.device_service import refresh_stale_device_statuses
from app.services.device_credentials import verify_device_token
from app.services.control_queue import control_queue
from app.services.rate_limit import device_rate_limiter
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/control", tags=["设备控制"])

# === 内存中的控制指令队列 ===
# 存储待执行的指令，设备通过 control_pull 轮询拉取
# 格式：{device_id: [{"command": "light", "value": "on", "params": {}}]}
# MVP 使用内存队列，生产环境应替换为 Redis 或数据库持久化
command_queue = control_queue.memory_queues

SUPPORTED_CONTROL_COMMANDS = {
    "light": "on/off（灯光开关）",
    "color_temperature": "2700-6500（灯光色温，单位 K）",
    "light_brightness": "0-100（灯光亮度）",
    "wechat_notify": "on/off（微信消息通知）",
    "auto_screen_brightness": "on/off（自动屏幕亮度）",
    "focus_mode": "on/off（专注模式）",
    "screen_brightness": "0-100（手动屏幕亮度）",
}


@router.post("/{device_id}", response_model=ApiResponse)
async def send_control_command(
    device_id: str,
    command_data: dict,
    request: Request,
    device: Device = Depends(require_owned_device),
    db: AsyncSession = Depends(get_db),
):
    """
    用户下发控制指令（前端 → 后端 → 设备队列）
    POST /api/v1/control/{device_id}
    需要 JWT 认证

    支持的指令：
      - light: on/off（灯光开关）
      - color_temperature: 2700-6500（灯光色温，单位 K）
      - light_brightness: 0-100（灯光亮度）
      - wechat_notify: on/off（微信消息通知）
      - auto_screen_brightness: on/off（自动屏幕亮度）
      - focus_mode: on/off（专注模式）
      - screen_brightness: 0-100（手动屏幕亮度）

    流程：
    1. 验证设备是否绑定到当前用户
    2. 检查设备是否在线
    3. 将指令加入设备队列，等待设备轮询拉取

    错误码：
      3002 - 设备未绑定
      3003 - 设备已离线
    """
    # 验证设备绑定关系和在线状态
    await refresh_stale_device_statuses(db, [device])

    if device.status != "online":
        return ApiResponse(code=3003, message="设备已离线", data=None)

    # 提取指令参数
    command = command_data.get("command", "")
    value = command_data.get("value", "")
    params = command_data.get("params", {})

    if command not in SUPPORTED_CONTROL_COMMANDS:
        return ApiResponse(code=4001, message=f"不支持的控制指令：{command}", data=None)

    # 将指令加入该设备的队列
    command_id = await control_queue.enqueue(device_id, command, value, params)
    mqtt_payload = {
        "code": 200,
        "type": "control",
        "timestamp": int(time.time()),
        "command_id": command_id,
        "command": command,
        "value": value,
        "params": params,
    }
    log = OperationLog(
        user_id=device.bound_user_id,
        device_id=device_id,
        action=f"control_{command}",
        detail=json.dumps(
            {
                "command_id": command_id,
                "command": command,
                "value": value,
                "params": params,
                "channel": "queued",
            },
            ensure_ascii=False,
        ),
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    # 先落库审计记录，再执行 MQTT 这一外部副作用。
    await db.commit()

    channel = "mqtt"
    try:
        await mqtt_client.publish(
            get_control_topic(device_id),
            json.dumps(mqtt_payload, ensure_ascii=False).encode("utf-8"),
        )
    except RuntimeError:
        # MQTT 暂不可用时保留 Stream 中的指令，设备仍可通过 HTTP 拉取。
        channel = "http_pull"

    log.detail = json.dumps(
        {
            "command_id": command_id,
            "command": command,
            "value": value,
            "params": params,
            "channel": channel,
        },
        ensure_ascii=False,
    )
    await db.commit()

    return ApiResponse(
        message="指令已下发",
        data={"command_id": command_id, "channel": channel},
    )


@router.get("/{device_id}/pull")
async def pull_control_command(
    device_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
):
    """
    设备拉取控制指令（设备侧，Step 4）
    GET /api/v1/control/{device_id}/pull
    设备每 3 秒轮询一次，从队列中获取待执行指令

    认证：通过 URL Header 中的 Authorization: Bearer {device_token} 验证
    注意：Token 放在 Header 而非 URL 参数中

    响应：
      - 有待执行指令：pending=true + command/value/params
      - 无待执行指令：pending=false
    """
    await device_rate_limiter.check(
        f"control-pull:{device_id}:{request.client.host if request.client else 'unknown'}",
        limit=180,
    )
    # 从 Header 中解析设备 Token
    device_token = None
    if authorization and authorization.startswith("Bearer "):
        device_token = authorization[7:]

    # 验证设备 Token
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()

    if not verify_device_token(device, device_token):
        return {
            "code": 401,
            "msg": "无效的设备凭证",
            "data": None,
        }

    # 从队列中取出一条指令（FIFO）
    cmd = await control_queue.pull(device_id)
    if cmd:
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "pending": True,
                "command_id": cmd["command_id"],
                "command": cmd["command"],
                "value": cmd["value"],
                "params": cmd.get("params", {}),
            },
        }

    # 无待执行指令
    return {
        "code": 0,
        "msg": "success",
        "data": {"pending": False},
    }


@router.post("/{device_id}/ack", response_model=ApiResponse)
async def control_acknowledge(
    device_id: str,
    ack_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    设备控制执行结果通知（可选）
    POST /api/v1/control/{device_id}/ack

    设备执行完控制指令后回调，通知后端指令执行结果
    前端可通过 WebSocket 接收执行结果更新

    请求体示例：
    {
        "token": "dev_xxx",
        "timestamp": 1713880040,
        "type": "control_ack",
        "command": "light",
        "result": "success"
    }
    """
    await device_rate_limiter.check(
        f"control-ack:{device_id}:{request.client.host if request.client else 'unknown'}",
        limit=180,
    )
    token = ack_data.get("token", "")
    command_id = str(ack_data.get("command_id") or "")
    command = ack_data.get("command", "")
    result_status = ack_data.get("result", "")

    # 验证设备 Token
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()

    if not verify_device_token(device, token):
        raise HTTPException(status_code=401, detail="无效的设备凭证")

    if command_id:
        await control_queue.acknowledge(device_id, command_id)
    await ws_manager.broadcast_control_result(
        device_id,
        command,
        str(ack_data.get("value") or ""),
        result_status,
    )

    return ApiResponse(message="执行结果已接收")
