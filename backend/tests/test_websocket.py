import json

import pytest
from sqlalchemy import select

from app.config import settings
from app.models.device import Device
from app.models.user import User
from app.main import websocket_endpoint
from app.websocket.handlers import can_user_subscribe_to_device
from app.websocket.manager import WebSocketManager


class FakeWebSocket:
    def __init__(self):
        self.messages: list[dict] = []
        self.closed: tuple[int, str] | None = None

    async def accept(self):
        return None

    async def close(self, code: int, reason: str):
        self.closed = (code, reason)

    async def send_text(self, message: str):
        self.messages.append(json.loads(message))


class EndpointWebSocket(FakeWebSocket):
    def __init__(self, incoming: list[str]):
        super().__init__()
        self.incoming = incoming
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def receive_text(self) -> str:
        return self.incoming.pop(0)


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
async def test_websocket_caps_unauthenticated_connections():
    manager = WebSocketManager()
    sockets = [FakeWebSocket() for _ in range(3)]
    previous_limit = settings.WS_MAX_UNAUTHENTICATED_CONNECTIONS
    settings.WS_MAX_UNAUTHENTICATED_CONNECTIONS = 2
    try:
        assert await manager.connect(sockets[0]) is True
        assert await manager.connect(sockets[1]) is True
        assert await manager.connect(sockets[2]) is False
        assert sockets[2].closed == (1013, "待认证连接数已达上限")
        assert sockets[2] not in manager.active_connections
    finally:
        settings.WS_MAX_UNAUTHENTICATED_CONNECTIONS = previous_limit


@pytest.mark.asyncio
async def test_websocket_endpoint_closes_after_failed_first_message_authentication():
    websocket = EndpointWebSocket([
        json.dumps({"type": "auth", "token": "invalid-token"}),
    ])
    await websocket_endpoint(websocket)
    assert websocket.accepted is True
    assert websocket.closed == (1008, "认证失败")


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
