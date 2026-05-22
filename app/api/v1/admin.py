from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.device import Device
from app.models.user import User
from app.models.sensor_data import SensorData
from app.schemas.base import ApiResponse

router = APIRouter(prefix="/admin", tags=["管理员"])


@router.get("/users", response_model=ApiResponse)
async def list_all_users(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取所有用户列表"""
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    user_list = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]
    return ApiResponse(data=user_list)


@router.put("/users/{user_id}/status", response_model=ApiResponse)
async def toggle_user_status(
    user_id: int,
    status_data: dict,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """启用/禁用用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return ApiResponse(code=2002, message="用户不存在", data=None)
    if user.role == "admin":
        return ApiResponse(code=4003, message="不能禁用管理员", data=None)

    user.is_active = status_data.get("is_active", True)
    await db.flush()
    return ApiResponse(message="用户状态已更新")


@router.get("/devices", response_model=ApiResponse)
async def list_all_devices(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取所有设备列表"""
    result = await db.execute(select(Device).order_by(Device.id))
    devices = result.scalars().all()
    device_list = [
        {
            "id": d.id,
            "device_id": d.device_id,
            "device_name": d.device_name,
            "status": d.status,
            "bound_user_id": d.bound_user_id,
            "chip_model": d.chip_model,
            "firmware_version": d.firmware_version,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
        }
        for d in devices
    ]
    return ApiResponse(data=device_list)


@router.delete("/devices/{device_id}", response_model=ApiResponse)
async def force_delete_device(
    device_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """强制删除设备（管理员）"""
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        return ApiResponse(code=3001, message="设备不存在", data=None)

    await db.delete(device)
    await db.flush()
    return ApiResponse(message="设备已删除")


@router.get("/stats", response_model=ApiResponse)
async def system_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """系统统计概览"""
    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    device_count = (await db.execute(select(func.count(Device.id)))).scalar() or 0
    online_count = (
        await db.execute(select(func.count(Device.id)).where(Device.status == "online"))
    ).scalar() or 0
    data_count = (await db.execute(select(func.count(SensorData.id)))).scalar() or 0

    return ApiResponse(data={
        "user_count": user_count,
        "device_count": device_count,
        "online_count": online_count,
        "data_count": data_count,
    })
