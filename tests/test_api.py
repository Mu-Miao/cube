from types import SimpleNamespace

import pytest

from app.api.v1.control import pull_control_command, send_control_command
from app.models.device import Device
from app.models.user import User


@pytest.mark.asyncio
async def test_device_pulls_control_command_with_authorization_header(db_session):
    user = User(username="alice", password="hashed-password")
    device = Device(
        device_id="TEST-CUBE-CTRL",
        device_name="测试魔方",
        token="dev_test_token",
        status="online",
        bound_user_id=1,
    )
    db_session.add_all([user, device])
    await db_session.flush()
    device.bound_user_id = user.id
    await db_session.flush()

    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
    response = await send_control_command(
        "TEST-CUBE-CTRL",
        {"command": "light", "value": "on"},
        request,
        user,
        db_session,
    )

    assert response.code == 0

    pulled = await pull_control_command(
        "TEST-CUBE-CTRL",
        db_session,
        authorization="Bearer dev_test_token",
    )

    assert pulled["code"] == 0
    assert pulled["data"]["pending"] is True
    assert pulled["data"]["command"] == "light"
    assert pulled["data"]["value"] == "on"
