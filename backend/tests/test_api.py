# tests/test_api.py
# API 集成测试

import json
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ota_log import OtaLog
from app.models.user import User
from app.mqtt.client import MQTTClient
from app.mqtt.handlers import _handle_control_ack, _latest_firmware


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
                "pm25": 21.7,
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
    assert data["pm25"] == 21.7

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
    first_command_id = resp.json()["data"]["command_id"]
    assert resp.json()["data"]["channel"] == "http_pull"

    resp = await client.get(
        f"/api/v1/control/{device_id}/pull",
        headers={"Authorization": f"Bearer {device_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["pending"] is True
    assert body["data"]["command_id"] == first_command_id
    assert body["data"]["command"] == "light"
    assert body["data"]["value"] == "on"

    ack = await client.post(
        f"/api/v1/control/{device_id}/ack",
        json={
            "token": device_token,
            "command_id": first_command_id,
            "command": "light",
            "value": "on",
            "result": "success",
        },
    )
    assert ack.status_code == 200

    resp = await client.post(
        f"/api/v1/control/{device_id}",
        json={
            "command": "color_temperature",
            "value": "3000",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "指令已下发"

    resp = await client.post(
        f"/api/v1/control/{device_id}",
        json={
            "command": "auto_screen_brightness",
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
    assert body["data"]["command"] == "color_temperature"
    assert body["data"]["value"] == "3000"

    resp = await client.get(
        f"/api/v1/control/{device_id}/pull",
        headers={"Authorization": f"Bearer {device_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["pending"] is True
    assert body["data"]["command"] == "auto_screen_brightness"
    assert body["data"]["value"] == "on"

    resp = await client.post(
        f"/api/v1/control/{device_id}",
        json={
            "command": "buzzer",
            "value": "on",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 4001


@pytest.mark.asyncio
async def test_ota_push_publishes_hardware_payload(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "ota_admin",
            "password": "test123456",
        },
    )
    result = await db_session.execute(select(User).where(User.username == "ota_admin"))
    admin = result.scalar_one()
    admin.role = "admin"
    await db_session.flush()

    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "ota_admin",
            "password": "test123456",
        },
    )
    headers = {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}

    device_id = "OTA001"
    handshake_response = await client.post(
        "/api/v1/device/auth",
        json={
            "device_id": device_id,
            "timestamp": 1713880000,
            "type": "handshake",
            "chip_model": "ESP32-S3",
            "version": "1.0.0",
        },
    )
    device_token = handshake_response.json()["token"]

    published: list[tuple[str, bytes]] = []

    async def fake_publish(topic: str, payload: bytes) -> None:
        published.append((topic, payload))

    monkeypatch.setattr("app.api.v1.ota.mqtt_client.publish", fake_publish)

    resp = await client.post(
        "/api/v1/ota/push",
        json={
            "device_id": device_id,
            "version": "1.1.0",
            "url": "https://tianmuzc.site/firmware/v1.1.0.bin",
            "md5": "d41d8cd98f00b204e9800998ecf8427e",
        },
        headers=headers,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["pushed"] == 1
    assert published[0][0] == "cube2026/server/OTA001/control"

    payload = json.loads(published[0][1].decode("utf-8"))
    assert payload["timestamp"] > 0
    assert payload == {
        "code": 200,
        "type": "ota_update",
        "msg": "新版本可用",
        "timestamp": payload["timestamp"],
        "url": "https://tianmuzc.site/firmware/v1.1.0.bin",
        "version": "1.1.0",
        "md5": "d41d8cd98f00b204e9800998ecf8427e",
    }

    @asynccontextmanager
    async def use_test_session():
        yield db_session

    async def fake_broadcast(*_args) -> None:
        return None

    monkeypatch.setattr("app.mqtt.handlers.async_session_factory", use_test_session)
    monkeypatch.setattr("app.mqtt.handlers.ws_manager.broadcast_control_result", fake_broadcast)

    await _handle_control_ack(
        device_id,
        {
            "token": device_token,
            "command": "ota_update",
            "value": "1.1.0",
            "result": "success",
            "message": "firmware flashed and rebooted",
        },
    )
    ota_log = (
        await db_session.execute(
            select(OtaLog).where(
                OtaLog.device_id == device_id,
                OtaLog.target_version == "1.1.0",
            )
        )
    ).scalar_one()
    assert ota_log.status == "success"
    assert ota_log.remark == "firmware flashed and rebooted"

    async def failed_publish(_topic: str, _payload: bytes) -> None:
        raise RuntimeError("MQTT 未连接，消息未发送")

    monkeypatch.setattr("app.api.v1.ota.mqtt_client.publish", failed_publish)
    failed_resp = await client.post(
        "/api/v1/ota/push",
        json={
            "device_id": device_id,
            "version": "1.2.0",
            "url": "https://tianmuzc.site/firmware/v1.2.0.bin",
            "md5": "d41d8cd98f00b204e9800998ecf8427e",
        },
        headers=headers,
    )
    assert failed_resp.json()["code"] == 500
    assert failed_resp.json()["message"] == "固件推送失败，请检查 MQTT 连接"


@pytest.mark.asyncio
async def test_mqtt_publish_rejects_disconnected_client():
    client = MQTTClient()

    with pytest.raises(RuntimeError, match="MQTT 未连接"):
        await client.publish("cube2026/server/OTA001/control", b"{}")


@pytest.mark.asyncio
async def test_ota_firmware_upload_returns_public_url(
    client: AsyncClient,
    db_session: AsyncSession,
):
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "firmware_admin",
            "password": "test123456",
        },
    )
    result = await db_session.execute(select(User).where(User.username == "firmware_admin"))
    admin = result.scalar_one()
    admin.role = "admin"
    await db_session.flush()

    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "firmware_admin",
            "password": "test123456",
        },
    )
    headers = {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}

    resp = await client.post(
        "/api/v1/ota/firmware",
        params={"version": "1.1.0"},
        files={"file": ("firmware.bin", b"test-firmware", "application/octet-stream")},
        headers=headers,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["url"].startswith(
        "https://tianmuzc.site/api/v1/ota/firmware/v1.1.0.bin?"
    )
    assert "expires=" in body["data"]["url"]
    assert "signature=" in body["data"]["url"]
    assert body["data"]["md5"] == "b1d9cbf0a8651c78ccd96a1e8b32a50f"
    assert body["data"]["size"] == len(b"test-firmware")
    signed_url = urlsplit(body["data"]["url"])
    download = await client.get(f"{signed_url.path}?{signed_url.query}")
    assert download.status_code == 200
    assert download.content == b"test-firmware"
    tampered = await client.get(
        f"{signed_url.path}?{signed_url.query.replace('signature=', 'signature=bad')}"
    )
    assert tampered.status_code == 403
    firmware_path = Path("data/firmware/v1.1.0.bin")
    if firmware_path.exists():
        firmware_path.unlink()


def test_latest_firmware_builds_version_check_response_source():
    firmware_dir = Path("data/firmware")
    firmware_dir.mkdir(parents=True, exist_ok=True)
    firmware_path = firmware_dir / "firmware_v9.9.9.bin"
    firmware_path.write_bytes(b"version-check-firmware")
    try:
        latest = _latest_firmware()
    finally:
        firmware_path.unlink()

    assert latest is not None
    assert latest[0] == "9.9.9"
    assert latest[1].startswith(
        "https://tianmuzc.site/api/v1/ota/firmware/firmware_v9.9.9.bin?"
    )
    assert "expires=" in latest[1] and "signature=" in latest[1]
    assert latest[2] == "c29a11009a9e73ce1b4057f11d284ff5"


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

    resp = await client.get(
        f"/api/v1/data/{device_id}/trend",
        params={"hours": 1},
        headers=headers,
    )
    assert resp.status_code == 200
    trend_data = resp.json()["data"]
    assert sum(item["sample_count"] for item in trend_data) == 3
    assert [item["timestamp"] for item in trend_data] == sorted(
        item["timestamp"] for item in trend_data
    )


@pytest.mark.asyncio
async def test_data_upload_accepts_nested_hardware_payload(client: AsyncClient):
    device_id = "NESTED01"
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "nested_user",
            "password": "test123456",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "nested_user",
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
            "version": "v0.9.0",
        },
    )
    device_token = resp.json()["token"]

    await client.post(
        "/api/v1/device/bind",
        json={
            "device_id": device_id,
            "device_name": "嵌套数据设备",
        },
        headers=headers,
    )

    resp = await client.post(
        "/api/v1/data/upload",
        json={
            "device_id": device_id,
            "token": device_token,
            "timestamp": int(time.time()),
            "type": "data_report",
            "data": {
                "data": {
                    "temperature": 26.8,
                    "humidity": 58.5,
                    "illuminance": 520,
                    "aqi": 42,
                    "pm2.5": 18.6,
                    "tvoc": 160,
                    "eco2": 680,
                    "mold_risk": 0,
                    "gas": 0,
                    "version": "1.0",
                },
                "status": {
                    "wifi_connected": True,
                    "mqtt_connected": True,
                    "screen_normal": True,
                    "sensor_normal": True,
                    "light": "on",
                    "light_brightness": "80",
                    "color_temperature": 3000,
                    "wechat_notify": False,
                    "auto_screen_brightness": True,
                    "screen_brightness": "60",
                    "focus_mode": True,
                },
            },
        },
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 200

    resp = await client.get(f"/api/v1/data/{device_id}/latest", headers=headers)
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["temperature"] == 26.8
    assert body["data"]["humidity"] == 58.5
    assert body["data"]["pm25"] == 18.6
    assert body["data"]["light"] is True
    assert body["data"]["light_brightness"] == 80
    assert body["data"]["color_temperature"] == 3000
    assert body["data"]["wechat_notify"] is False
    assert body["data"]["auto_screen_brightness"] is True
    assert body["data"]["screen_brightness"] == 60
    assert body["data"]["focus_mode"] is True
    assert body["data"]["wifi_rssi"] is None

    resp = await client.get("/api/v1/device/list", headers=headers)
    devices = resp.json()["data"]
    target = next(device for device in devices if device["device_id"] == device_id)
    assert target["firmware_version"] == "1.0"


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
