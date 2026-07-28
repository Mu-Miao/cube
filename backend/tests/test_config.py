import pytest

from app.config import settings, validate_runtime_settings


def test_sqlite_rejects_multiple_workers(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", "sqlite+aiosqlite:///./data/test.db")
    monkeypatch.setattr(settings, "WEB_CONCURRENCY", 2)

    with pytest.raises(RuntimeError, match="SQLite"):
        validate_runtime_settings()


def test_production_rejects_public_mqtt_broker(monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "WEB_CONCURRENCY", 2)
    monkeypatch.setattr(
        settings,
        "DATABASE_URL",
        "postgresql+asyncpg://cube:password@127.0.0.1:5432/cube",
    )
    monkeypatch.setattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0")
    monkeypatch.setattr(settings, "MQTT_BROKER_URL", "broker.emqx.io")

    with pytest.raises(RuntimeError, match="私有 MQTT"):
        validate_runtime_settings()


def test_valid_production_runtime_settings(monkeypatch):
    values = {
        "DEBUG": False,
        "WEB_CONCURRENCY": 4,
        "DATABASE_URL": "postgresql+asyncpg://cube:password@127.0.0.1:5432/cube",
        "REDIS_URL": "redis://127.0.0.1:6379/0",
        "MQTT_BROKER_URL": "mqtt.internal.example",
        "MQTT_BROKER_PORT": 8883,
        "MQTT_TLS": True,
        "MQTT_USERNAME": "cube",
        "MQTT_PASSWORD": "strong-password",
        "MQTT_CA_CERT": "/run/secrets/mqtt-ca.crt",
        "FIRMWARE_PUBLIC_BASE_URL": "https://cube.example/",
        "CORS_ORIGINS": ["https://cube.example"],
        "DEMO_MODE": False,
        "REFRESH_COOKIE_SECURE": True,
    }
    for name, value in values.items():
        monkeypatch.setattr(settings, name, value)

    validate_runtime_settings()
