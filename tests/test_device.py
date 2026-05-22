import time

import pytest
from sqlalchemy import select

from app.api.v1.device import device_handshake
from app.models.device import Device
from app.schemas.device import DeviceHandshake


@pytest.mark.asyncio
async def test_device_handshake_creates_device_and_token(db_session):
    payload = DeviceHandshake(
        device_id="TEST-CUBE-001",
        timestamp=int(time.time()),
        chip_model="ESP32-S3",
        version="1.0.0",
    )

    ack = await device_handshake(payload, db_session)

    assert ack.code == 200
    assert ack.token.startswith("dev_")

    result = await db_session.execute(
        select(Device).where(Device.device_id == "TEST-CUBE-001")
    )
    device = result.scalar_one()
    assert device.status == "online"
    assert device.token == ack.token
