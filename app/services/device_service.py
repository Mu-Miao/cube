# app/services/device_service.py
# 设备服务
# 处理设备绑定、解绑等业务逻辑

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device


async def unbind_device(db: AsyncSession, device_id: str, user_id: int) -> tuple[int, str]:
    """
    解绑设备

    流程：
    1. 查询设备是否存在
    2. 检查设备是否绑定到当前用户
    3. 将 bound_user_id 设为 null
    4. 将 status 设为 "offline"
    5. 保存到数据库

    Args:
        db: 数据库会话
        device_id: 设备唯一标识
        user_id: 当前用户 ID

    Returns:
        (code, message) 元组：
          (0, "解绑成功") - 成功
          (3001, "设备不存在") - 设备不存在
          (3002, "设备未绑定到当前用户") - 设备未绑定到当前用户
    """
    # 查询设备是否存在
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        return 3001, "设备不存在"

    # 检查设备是否绑定到当前用户
    if device.bound_user_id != user_id:
        return 3002, "设备未绑定到当前用户"

    # 执行解绑：清除绑定关系，设置离线状态
    device.bound_user_id = None
    device.status = "offline"
    await db.flush()

    return 0, "解绑成功"
