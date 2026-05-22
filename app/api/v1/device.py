# app/api/v1/device.py
# 设备管理接口
# 提供：设备握手、心跳、绑定、设备列表

import secrets
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.device import Device
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.device import (
    DeviceHandshake, DeviceHandshakeAck, DeviceHeartbeat,
    DeviceBind, DeviceUnbind, DeviceItem,
)
from app.services.device_service import unbind_device

router = APIRouter(prefix="/device", tags=["设备管理"])

# 设备 Token 过期时间（秒），24 小时
DEVICE_TOKEN_EXPIRE = 86400


@router.post("/auth", response_model=DeviceHandshakeAck)
async def device_handshake(payload: DeviceHandshake, db: AsyncSession = Depends(get_db)):
    """
    设备握手接口（Step 1）
    POST /api/v1/device/auth

    设备首次连接时调用，注册设备信息并返回临时 Token
    支持 MQTT 和 HTTP 两种方式接入

    流程：
    1. 查找设备是否已存在
    2. 若不存在则创建设备记录
    3. 若已存在则更新芯片型号和固件版本
    4. 生成新的设备 Token 并返回
    """
    # 查询设备是否已存在
    result = await db.execute(select(Device).where(Device.device_id == payload.device_id))
    device = result.scalar_one_or_none()

    if device is None:
        # 新设备：创建设备记录
        device = Device(
            device_id=payload.device_id,
            chip_model=payload.chip_model,
            firmware_version=payload.version,
        )
        db.add(device)
    else:
        # 已有设备：更新硬件信息
        device.chip_model = payload.chip_model
        device.firmware_version = payload.version

    # 生成设备 Token（格式：dev_随机32位十六进制）
    device_token = f"dev_{secrets.token_hex(16)}"
    device.token = device_token
    device.status = "online"
    device.last_seen = datetime.now(timezone.utc)

    await db.flush()

    return DeviceHandshakeAck(
        code=200,
        msg="握手成功",
        timestamp=int(time.time()),
        token=device_token,
        expire_time=DEVICE_TOKEN_EXPIRE,
    )


@router.post("/{device_id}/heartbeat")
async def device_heartbeat(payload: DeviceHeartbeat, db: AsyncSession = Depends(get_db)):
    """
    设备心跳接口（Step 2，设备每 30 秒调用一次）
    POST /api/v1/device/{device_id}/heartbeat

    用于维持设备在线状态，更新 last_seen 时间戳
    验证设备 Token 确保请求合法
    """
    # 查询设备并验证 Token
    result = await db.execute(select(Device).where(Device.device_id == payload.device_id))
    device = result.scalar_one_or_none()

    if not device or device.token != payload.token:
        raise HTTPException(status_code=401, detail="无效的设备凭证")

    # 更新设备在线状态和最后在线时间
    device.status = "online"
    device.last_seen = datetime.now(timezone.utc)
    await db.flush()

    return {
        "code": 200,
        "type": "heartbeat_ack",
        "msg": "ok",
        "timestamp": int(time.time()),
    }


@router.post("/bind", response_model=ApiResponse)
async def bind_device(
    bind_data: DeviceBind,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    用户绑定设备接口
    POST /api/v1/device/bind
    需要 JWT 认证

    流程：
    1. 查询设备是否存在（设备需先握手上线）
    2. 检查设备是否已绑定到其他用户
    3. 将设备绑定到当前用户

    错误码：
      3001 - 设备不存在
      3004 - 设备已绑定到其他用户
    """
    result = await db.execute(select(Device).where(Device.device_id == bind_data.device_id))
    device = result.scalar_one_or_none()

    if not device:
        return ApiResponse(code=3001, message="设备不存在", data=None)

    # 检查是否已绑定到其他用户
    if device.bound_user_id and device.bound_user_id != current_user.id:
        return ApiResponse(code=3004, message="设备已绑定到其他用户", data=None)

    # 绑定设备
    device.bound_user_id = current_user.id
    device.device_name = bind_data.device_name
    await db.flush()

    return ApiResponse(message="绑定成功")


@router.get("/list", response_model=ApiResponse[list[DeviceItem]])
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的设备列表
    GET /api/v1/device/list
    需要 JWT 认证

    返回当前用户绑定的所有设备及其在线状态
    """
    result = await db.execute(
        select(Device).where(Device.bound_user_id == current_user.id)
    )
    devices = result.scalars().all()

    device_list = [
        DeviceItem(
            device_id=d.device_id,
            device_name=d.device_name,
            status=d.status,
            last_seen=d.last_seen,
            chip_model=d.chip_model,
            firmware_version=d.firmware_version,
        )
        for d in devices
    ]
    return ApiResponse(data=device_list)


@router.post("/unbind", response_model=ApiResponse)
async def unbind_device_endpoint(
    unbind_data: DeviceUnbind,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    用户解绑设备接口
    POST /api/v1/device/unbind
    需要 JWT 认证

    流程：
    1. 查询设备是否存在
    2. 检查设备是否绑定到当前用户
    3. 清除绑定关系，将设备状态设为 offline

    错误码：
      3001 - 设备不存在
      3002 - 设备未绑定到当前用户
    """
    code, message = await unbind_device(db, unbind_data.device_id, current_user.id)
    return ApiResponse(code=code, message=message, data=None)


@router.put("/{device_id}/rename", response_model=ApiResponse)
async def rename_device(
    device_id: str,
    rename_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """重命名设备 PUT /api/v1/device/{device_id}/rename"""
    result = await db.execute(
        select(Device).where(
            Device.device_id == device_id,
            Device.bound_user_id == current_user.id,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        return ApiResponse(code=3002, message="设备未绑定", data=None)

    new_name = rename_data.get("device_name", "").strip()
    if not new_name:
        return ApiResponse(code=400, message="设备名称不能为空", data=None)

    device.device_name = new_name
    await db.flush()
    return ApiResponse(message="设备名称已更新")
