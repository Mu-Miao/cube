# tests/test_device.py
# 设备模块测试

import pytest
from httpx import AsyncClient


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
