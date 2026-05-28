import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.operation_log import OperationLog
from app.models.sensor_data import SensorData
from app.models.user import User
from app.models.voice_log import VoiceLog
from scripts.seed_demo import DEMO_DEVICES, DEMO_PASSWORD, seed_demo_data


@pytest.mark.asyncio
async def test_seed_demo_data_is_idempotent(db_session: AsyncSession):
    first = await seed_demo_data(db_session)
    second = await seed_demo_data(db_session)

    assert first["password"] == DEMO_PASSWORD
    assert second["devices"] == len(DEMO_DEVICES)

    users = (
        await db_session.execute(
            select(User).where(User.username.in_(["demo", "admin"]))
        )
    ).scalars().all()
    assert {user.username for user in users} == {"demo", "admin"}
    assert next(user for user in users if user.username == "admin").role == "admin"

    devices = (
        await db_session.execute(
            select(Device).where(
                Device.device_id.in_([device.device_id for device in DEMO_DEVICES])
            )
        )
    ).scalars().all()
    assert len(devices) == len(DEMO_DEVICES)
    assert {device.bound_user_id for device in devices} == {
        next(user.id for user in users if user.username == "demo")
    }

    sensor_count = (
        await db_session.execute(select(func.count(SensorData.id)))
    ).scalar_one()
    operation_count = (
        await db_session.execute(select(func.count(OperationLog.id)))
    ).scalar_one()
    voice_count = (
        await db_session.execute(select(func.count(VoiceLog.id)))
    ).scalar_one()

    assert sensor_count == second["sensor_rows"]
    assert operation_count == second["operation_logs"]
    assert voice_count == second["voice_logs"]
