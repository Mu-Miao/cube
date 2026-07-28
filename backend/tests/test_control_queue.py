import pytest

from app.config import settings
from app.services.control_queue import control_queue


@pytest.mark.asyncio
async def test_memory_control_queue_retries_then_expires(monkeypatch):
    monkeypatch.setattr(settings, "CONTROL_ACK_TIMEOUT_SECONDS", 0)
    monkeypatch.setattr(settings, "CONTROL_MAX_RETRIES", 2)

    command_id = await control_queue.enqueue(
        "RETRY-DEVICE",
        "light",
        "on",
        {},
    )

    first = await control_queue.pull("RETRY-DEVICE")
    retry = await control_queue.pull("RETRY-DEVICE")
    expired = await control_queue.pull("RETRY-DEVICE")

    assert first is not None
    assert first["command_id"] == command_id
    assert first["attempts"] == 1
    assert retry is not None
    assert retry["command_id"] == command_id
    assert retry["attempts"] == 2
    assert expired is None
    assert command_id not in control_queue.memory_inflight["RETRY-DEVICE"]


@pytest.mark.asyncio
async def test_memory_control_queue_acknowledges_by_command_id():
    command_id = await control_queue.enqueue(
        "ACK-DEVICE",
        "buzzer",
        "off",
        {},
    )
    await control_queue.pull("ACK-DEVICE")

    assert await control_queue.acknowledge("ACK-DEVICE", command_id) is True
    assert await control_queue.acknowledge("ACK-DEVICE", command_id) is False
