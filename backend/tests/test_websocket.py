import json

import pytest
from sqlalchemy import select

from app.models.device import Device
from app.models.user import User
from app.websocket.handlers import can_user_subscribe_to_device
from app.websocket.manager import WebSocketManager


class FakeWebSocket:
    def __init__(self):
        self.messages: list[dict] = []

    async def accept(self):
        return None

    async def send_text(self, message: str):
        self.messages.append(json.loads(message))


@pytest.mark.asyncio
async def test_websocket_rejects_subscription_before_authentication():
    manager = WebSocketManager()
    websocket = FakeWebSocket()
    await manager.connect(websocket)

    await manager.subscribe(websocket, "DEVICE-001")

    assert websocket.messages[-1] == {
        "type": "subscribe_result",
        "code": 1002,
        "message": "请先完成认证",
    }
    assert manager.active_connections[websocket]["device_ids"] == set()


@pytest.mark.asyncio
async def test_websocket_device_subscription_checks_owner(db_session):
    owner = User(username="ws_owner", password="hashed")
    other_user = User(username="ws_other", password="hashed")
    db_session.add_all([owner, other_user])
    await db_session.flush()

    device = Device(
        device_id="WS-OWNED-001",
        device_name="WebSocket 测试设备",
        bound_user_id=owner.id,
    )
    db_session.add(device)
    await db_session.flush()

    assert await can_user_subscribe_to_device(
        db_session,
        owner.id,
        device.device_id,
    )
    assert not await can_user_subscribe_to_device(
        db_session,
        other_user.id,
        device.device_id,
    )

    stored_device = await db_session.scalar(
        select(Device).where(Device.device_id == device.device_id)
    )
    assert stored_device is device
