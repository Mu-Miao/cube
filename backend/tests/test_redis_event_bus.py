import asyncio

import pytest

from app.config import settings
from app.services.redis_event_bus import RedisEventBus


class _FakePubSub:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.closed = False

    async def subscribe(self, _channel: str) -> None:
        if self.fail:
            raise ConnectionError("redis unavailable")

    async def get_message(self, **_kwargs):
        return {
            "data": (
                '{"origin":"another-worker","device_id":"cube-1","message":"online"}'
            )
        }

    async def unsubscribe(self, _channel: str) -> None:
        return None

    async def aclose(self) -> None:
        self.closed = True


class _FakeRedis:
    def __init__(self, pubsub: _FakePubSub) -> None:
        self._pubsub = pubsub
        self.closed = False

    def pubsub(self) -> _FakePubSub:
        return self._pubsub

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_redis_listener_reconnects_after_connection_failure(monkeypatch):
    monkeypatch.setattr(settings, "REDIS_URL", "redis://test")
    bus = RedisEventBus()
    failed = _FakeRedis(_FakePubSub(fail=True))
    recovered = _FakeRedis(_FakePubSub())
    clients = iter((failed, recovered))

    async def fake_client():
        bus._redis = next(clients)
        return bus._redis

    real_sleep = asyncio.sleep

    async def no_wait(_seconds: float) -> None:
        await real_sleep(0)

    received: list[tuple[str, str]] = []

    async def handler(device_id: str, message: str) -> None:
        received.append((device_id, message))
        bus._running = False

    monkeypatch.setattr(bus, "_client", fake_client)
    monkeypatch.setattr(
        "app.services.redis_event_bus.asyncio.sleep",
        no_wait,
    )

    await bus.listen(handler)

    assert received == [("cube-1", "online")]
    assert bus.failure_count == 1
    assert bus.last_error is None
    assert failed.closed is True
