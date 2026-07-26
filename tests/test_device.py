# tests/test_device.py
# 设备模块测试

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device


@pytest.mark.asyncio
async def test_device_handshake_new(client: AsyncClient):
    resp = await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": "AABBCCDDEE01",
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200
    assert body["token"].startswith("dev_")
    assert body["expire_time"] == 86400


@pytest.mark.asyncio
async def test_device_handshake_update(client: AsyncClient):
    device_id = "AABBCCDDEE02"
    first_resp = await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )
    resp = await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880100,
            "type": "handshake",
            "chip_model": "ESP32-C6",
            "version": "v2.0.0",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token"].startswith("dev_")
    assert body["token"] == first_resp.json()["token"]


@pytest.mark.asyncio
async def test_device_heartbeat(client: AsyncClient):
    device_id = "AABBCCDDEE03"
    handshake = await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )
    token = handshake.json()["token"]

    resp = await client.post(
        f"/api/v1/device/{device_id}/heartbeat",
        json={
            "device_id": device_id,
            "token": token,
            "timestamp": 1713880030,
            "type": "heartbeat",
            "status": {"wifi_connected": True, "screen_normal": True},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200


@pytest.mark.asyncio
async def test_device_heartbeat_syncs_control_status(
    client: AsyncClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    from app.api.v1 import device as device_api

    device_id = "AABBCCDDEE_HEARTBEAT_STATUS"
    handshake = await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )
    token = handshake.json()["token"]
    await client.post(
        "/api/v1/device/bind",
        json={"device_id": device_id, "device_name": "心跳状态设备"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/data/upload",
        json={
            "device_id": device_id,
            "token": token,
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "type": "data_report",
            "data": {
                "temperature": 25,
                "humidity": 50,
                "illuminance": 400,
                "aqi": 45,
                "tvoc": 100,
                "eco2": 500,
                "mold_risk": 0,
                "gas": 0,
            },
            "status": {
                "light": False,
                "wechat_notify": False,
                "focus_mode": False,
            },
        },
    )

    broadcasts: list[tuple[str, dict]] = []

    async def capture_heartbeat(device_id: str, status: dict) -> None:
        broadcasts.append((device_id, status))

    monkeypatch.setattr(
        device_api.ws_manager,
        "broadcast_device_heartbeat",
        capture_heartbeat,
    )

    resp = await client.post(
        f"/api/v1/device/{device_id}/heartbeat",
        json={
            "device_id": device_id,
            "token": token,
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "type": "heartbeat",
            "status": {
                "light": "on",
                "focus_mode": True,
                "screen_brightness": "75",
            },
        },
    )
    assert resp.status_code == 200
    assert broadcasts == [
        (
            device_id,
            {
                "light": True,
                "focus_mode": True,
                "screen_brightness": 75,
            },
        )
    ]

    latest = await client.get(
        f"/api/v1/data/{device_id}/latest",
        headers=auth_headers,
    )
    latest_data = latest.json()["data"]
    assert latest_data["light"] is True
    assert latest_data["wechat_notify"] is False
    assert latest_data["focus_mode"] is True
    assert latest_data["screen_brightness"] == 75


@pytest.mark.asyncio
async def test_device_heartbeat_invalid_token(client: AsyncClient):
    resp = await client.post(
        "/api/v1/device/NONEXIST/heartbeat",
        json={
            "device_id": "NONEXIST",
            "token": "dev_badtoken",
            "timestamp": 1713880030,
            "type": "heartbeat",
            "status": {"wifi_connected": False},
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_bind_device_success(client: AsyncClient, auth_headers: dict):
    device_id = "AABBCCDDEE04"
    await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )

    resp = await client.post(
        "/api/v1/device/bind",
        json={
            "device_id": device_id,
            "device_name": "客厅魔方",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["message"] == "绑定成功"


@pytest.mark.asyncio
async def test_bind_nonexistent_device(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/device/bind",
        json={
            "device_id": "NONEXIST01",
            "device_name": "不存在",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 3001


@pytest.mark.asyncio
async def test_device_list(client: AsyncClient, auth_headers: dict):
    device_id = "AABBCCDDEE05"
    await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )
    await client.post(
        "/api/v1/device/bind",
        json={
            "device_id": device_id,
            "device_name": "测试设备",
        },
        headers=auth_headers,
    )

    resp = await client.get("/api/v1/device/list", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    devices = body["data"]
    assert isinstance(devices, list)
    assert any(d["device_id"] == device_id for d in devices)


@pytest.mark.asyncio
async def test_device_list_marks_stale_online_device_offline(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
):
    device_id = "AABBCCDDEE_STALE"
    await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )
    await client.post(
        "/api/v1/device/bind",
        json={
            "device_id": device_id,
            "device_name": "过期在线设备",
        },
        headers=auth_headers,
    )

    result = await db_session.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one()
    device.status = "online"
    device.last_seen = datetime.now(timezone.utc) - timedelta(minutes=10)
    await db_session.flush()

    resp = await client.get("/api/v1/device/list", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    stale_device = next(d for d in body["data"] if d["device_id"] == device_id)
    assert stale_device["status"] == "offline"
    assert device.status == "offline"


@pytest.mark.asyncio
async def test_device_list_keeps_stale_demo_device_online(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
):
    device_id = "DEMO-CUBE-STALE"
    await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )
    await client.post(
        "/api/v1/device/bind",
        json={
            "device_id": device_id,
            "device_name": "演示在线设备",
        },
        headers=auth_headers,
    )

    result = await db_session.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one()
    device.status = "online"
    device.last_seen = datetime.now(timezone.utc) - timedelta(days=1)
    await db_session.flush()

    resp = await client.get("/api/v1/device/list", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    demo_device = next(d for d in body["data"] if d["device_id"] == device_id)
    assert demo_device["status"] == "online"
    assert device.status == "online"


@pytest.mark.asyncio
async def test_data_upload_does_not_refresh_stale_device_online_status(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
):
    device_id = "AABBCCDDEE_DATA"
    handshake = await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )
    token = handshake.json()["token"]
    await client.post(
        "/api/v1/device/bind",
        json={
            "device_id": device_id,
            "device_name": "数据不刷新在线设备",
        },
        headers=auth_headers,
    )

    result = await db_session.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one()
    stale_last_seen = datetime.now(timezone.utc) - timedelta(minutes=10)
    device.status = "online"
    device.last_seen = stale_last_seen
    await db_session.flush()

    resp = await client.post(
        "/api/v1/data/upload",
        json={
            "device_id": device_id,
            "token": token,
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "type": "data_report",
            "data": {
                "temperature": 25.5,
                "humidity": 60.2,
                "illuminance": 450,
                "aqi": 75,
                "pm25": 21.7,
                "tvoc": 120,
                "eco2": 520,
                "mold_risk": 1,
                "gas": 0,
                "wifi_rssi": -42,
                "version": "v1.0.1",
            },
            "status": {"focus_mode": False},
        },
    )
    assert resp.status_code == 200
    assert device.status == "online"
    assert device.last_seen == stale_last_seen

    list_resp = await client.get("/api/v1/device/list", headers=auth_headers)
    listed_device = next(d for d in list_resp.json()["data"] if d["device_id"] == device_id)
    assert listed_device["status"] == "offline"
    assert device.status == "offline"


@pytest.mark.asyncio
async def test_unbind_device(client: AsyncClient, auth_headers: dict):
    device_id = "AABBCCDDEE06"
    await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )
    await client.post(
        "/api/v1/device/bind",
        json={
            "device_id": device_id,
            "device_name": "待解绑设备",
        },
        headers=auth_headers,
    )

    resp = await client.post(
        "/api/v1/device/unbind",
        json={
            "device_id": device_id,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0

    list_resp = await client.get("/api/v1/device/list", headers=auth_headers)
    devices = list_resp.json()["data"]
    assert not any(d["device_id"] == device_id for d in devices)
