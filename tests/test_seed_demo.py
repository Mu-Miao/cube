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


@pytest.mark.asyncio
async def test_online_demo_latest_generates_live_sample(client, db_session: AsyncSession):
    await seed_demo_data(db_session)
    before_count = (
        await db_session.execute(select(func.count(SensorData.id)))
    ).scalar_one()
    before_latest = (
        await db_session.execute(
            select(SensorData)
            .where(SensorData.device_id == "DEMO-CUBE-001")
            .order_by(SensorData.timestamp.desc())
            .limit(1)
        )
    ).scalar_one()

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "demo", "password": DEMO_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['data']['access_token']}"}

    resp = await client.get("/api/v1/data/DEMO-CUBE-001/latest", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["data"]["device_id"] == "DEMO-CUBE-001"
    after_count = (
        await db_session.execute(select(func.count(SensorData.id)))
    ).scalar_one()
    after_latest = (
        await db_session.execute(
            select(SensorData)
            .where(SensorData.device_id == "DEMO-CUBE-001")
            .order_by(SensorData.timestamp.desc())
            .limit(1)
        )
    ).scalar_one()
    assert after_count == before_count + 1
    assert after_latest.timestamp > before_latest.timestamp


@pytest.mark.asyncio
async def test_offline_demo_latest_does_not_generate_live_sample(client, db_session: AsyncSession):
    await seed_demo_data(db_session)
    before_count = (
        await db_session.execute(
            select(func.count(SensorData.id)).where(SensorData.device_id == "DEMO-CUBE-003")
        )
    ).scalar_one()

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "demo", "password": DEMO_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['data']['access_token']}"}

    resp = await client.get("/api/v1/data/DEMO-CUBE-003/latest", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["data"]["device_id"] == "DEMO-CUBE-003"
    after_count = (
        await db_session.execute(
            select(func.count(SensorData.id)).where(SensorData.device_id == "DEMO-CUBE-003")
        )
    ).scalar_one()
    assert after_count == before_count


@pytest.mark.asyncio
async def test_online_demo_latest_generates_first_sample_when_empty(client, db_session: AsyncSession):
    await seed_demo_data(db_session)
    await db_session.execute(
        SensorData.__table__.delete().where(SensorData.device_id == "DEMO-CUBE-001")
    )
    await db_session.flush()

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "demo", "password": DEMO_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['data']['access_token']}"}

    resp = await client.get("/api/v1/data/DEMO-CUBE-001/latest", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["device_id"] == "DEMO-CUBE-001"
    assert body["data"]["temperature"] is not None
    count = (
        await db_session.execute(
            select(func.count(SensorData.id)).where(SensorData.device_id == "DEMO-CUBE-001")
        )
    ).scalar_one()
    assert count == 1
