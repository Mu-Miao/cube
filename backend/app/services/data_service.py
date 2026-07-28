from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.sensor_data import SensorData


async def get_latest_data(db: AsyncSession, device_id: str, user_id: int):
    device = await _verify_device(db, device_id, user_id)
    if not device:
        return None, "设备未绑定"

    result = await db.execute(
        select(SensorData)
        .where(SensorData.device_id == device_id)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none(), None


async def get_history_data(
    db: AsyncSession,
    device_id: str,
    user_id: int,
    hours: int = 24,
    limit: int = 100,
):
    device = await _verify_device(db, device_id, user_id)
    if not device:
        return None, "设备未绑定"

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(SensorData)
        .where(
            SensorData.device_id == device_id,
            SensorData.timestamp >= since,
        )
        .order_by(SensorData.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all(), None


async def _verify_device(db: AsyncSession, device_id: str, user_id: int):
    result = await db.execute(
        select(Device).where(
            Device.device_id == device_id,
            Device.bound_user_id == user_id,
        )
    )
    return result.scalar_one_or_none()
