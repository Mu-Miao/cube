from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device


async def find_owned_device(
    db: AsyncSession,
    user_id: int,
    device_id: str,
) -> Device | None:
    return (
        await db.execute(
            select(Device).where(
                Device.device_id == device_id,
                Device.bound_user_id == user_id,
            )
        )
    ).scalar_one_or_none()
