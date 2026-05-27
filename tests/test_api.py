# tests/test_api.py
# API 集成测试

import time

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_device_lifecycle(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "integration_user",
            "password": "test123456",
        },
    )
    assert resp.status_code == 200

    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "integration_user",
            "password": "test123456",
        },
    )
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    device_id = "INTEGRATION01"
    resp = await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )
    device_token = resp.json()["token"]

    resp = await client.post(
        "/api/v1/device/bind",
        json={
            "device_id": device_id,
            "device_name": "集成测试设备",
        },
        headers=headers,
    )
    assert resp.json()["code"] == 0

    resp = await client.post(
        "/api/v1/data/upload",
        json={
            "device_id": device_id,
            "token": device_token,
            "timestamp": 1713880030,
            "type": "data_report",
            "data": {
                "temperature": 25.5,
                "humidity": 60.2,
                "illuminance": 450,
                "aqi": 75,
                "tvoc": 120,
                "eco2": 520,
                "mold_risk": 1,
                "gas": 0,
                "wifi_rssi": -42,
                "version": "v1.0.0",
            },
            "status": {"focus_mode": False},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 200

    resp = await client.get(f"/api/v1/data/{device_id}/latest", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["temperature"] == 25.5
    assert data["humidity"] == 60.2

    resp = await client.get("/api/v1/device/list", headers=headers)
    devices = resp.json()["data"]
    assert any(d["device_id"] == device_id for d in devices)


@pytest.mark.asyncio
async def test_control_command_flow(client: AsyncClient):
    device_id = "CONTROL01"
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "control_user",
            "password": "test123456",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "control_user",
            "password": "test123456",
        },
    )
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )
    device_token = resp.json()["token"]

    await client.post(
        "/api/v1/device/bind",
        json={
            "device_id": device_id,
            "device_name": "控制测试设备",
        },
        headers=headers,
    )

    await client.post(
        f"/api/v1/device/{device_id}/heartbeat",
        json={
            "device_id": device_id,
            "token": device_token,
            "timestamp": 1713880030,
            "type": "heartbeat",
            "status": {"wifi_connected": True},
        },
    )

    resp = await client.post(
        f"/api/v1/control/{device_id}",
        json={
            "command": "light",
            "value": "on",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "指令已下发"

    resp = await client.get(
        f"/api/v1/control/{device_id}/pull",
        headers={"Authorization": f"Bearer {device_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["pending"] is True
    assert body["data"]["command"] == "light"
    assert body["data"]["value"] == "on"


@pytest.mark.asyncio
async def test_data_history(client: AsyncClient):
    device_id = "HISTORY01"
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "history_user",
            "password": "test123456",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "history_user",
            "password": "test123456",
        },
    )
    headers = {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}

    resp = await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )
    device_token = resp.json()["token"]

    await client.post(
        "/api/v1/device/bind",
        json={
            "device_id": device_id,
            "device_name": "历史数据设备",
        },
        headers=headers,
    )

    now_ts = int(time.time())
    for i in range(3):
        await client.post(
            "/api/v1/data/upload",
            json={
                "device_id": device_id,
                "token": device_token,
                "timestamp": now_ts - (3 - i) * 5,
                "type": "data_report",
                "data": {
                    "temperature": 25.0 + i,
                    "humidity": 60.0,
                    "illuminance": 450,
                    "aqi": 75,
                    "tvoc": 120,
                    "eco2": 520,
                    "mold_risk": 1,
                    "gas": 0,
                    "wifi_rssi": -42,
                    "version": "v1.0.0",
                },
            },
        )

    resp = await client.get(
        f"/api/v1/data/{device_id}/history",
        params={"hours": 24, "limit": 10},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]) == 3


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ai_analysis_uses_latest_sensor_data(client: AsyncClient):
    device_id = "AI01"
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "ai_user",
            "password": "test123456",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "ai_user",
            "password": "test123456",
        },
    )
    headers = {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}

    resp = await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "v1.0.0",
        },
    )
    device_token = resp.json()["token"]

    await client.post(
        "/api/v1/device/bind",
        json={
            "device_id": device_id,
            "device_name": "AI 分析测试设备",
        },
        headers=headers,
    )

    await client.post(
        "/api/v1/data/upload",
        json={
            "device_id": device_id,
            "token": device_token,
            "timestamp": int(time.time()),
            "type": "data_report",
            "data": {
                "temperature": 30,
                "humidity": 72,
                "illuminance": 180,
                "aqi": 95,
                "tvoc": 650,
                "eco2": 1200,
                "mold_risk": 2,
                "gas": 0,
                "wifi_rssi": -42,
                "version": "v1.0.0",
            },
        },
    )

    score_resp = await client.get(f"/api/v1/ai/{device_id}/score", headers=headers)
    assert score_resp.status_code == 200
    score_body = score_resp.json()
    assert score_body["code"] == 0
    assert 0 < score_body["data"]["score"] < 100
    assert score_body["data"]["level"] in {"excellent", "good", "fair", "poor"}

    risks_resp = await client.get(f"/api/v1/ai/{device_id}/risks", headers=headers)
    risks_body = risks_resp.json()
    assert risks_body["code"] == 0
    assert risks_body["data"]["highest_level"] == "warning"
    assert any(risk["field"] == "eco2" for risk in risks_body["data"]["risks"])

    suggestions_resp = await client.get(f"/api/v1/ai/{device_id}/suggestions", headers=headers)
    suggestions_body = suggestions_resp.json()
    assert suggestions_body["code"] == 0
    assert len(suggestions_body["data"]["suggestions"]) > 0

    report_resp = await client.get(f"/api/v1/ai/{device_id}/weekly-report", headers=headers)
    report_body = report_resp.json()
    assert report_body["code"] == 0
    assert len(report_body["data"]["days"]) == 1
    assert report_body["data"]["days"][0]["sample_count"] == 1
