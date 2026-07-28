import random
from datetime import datetime, timezone

from app.config import settings
from app.models.device import Device
from app.models.sensor_data import SensorData


DEMO_REFRESH_INTERVAL_SECONDS = 4


def is_live_demo_device(device: Device) -> bool:
    enabled = settings.DEBUG or settings.DEMO_MODE
    return (
        enabled
        and device.device_id.startswith("DEMO-CUBE-")
        and device.status == "online"
    )


def timestamp_age_seconds(timestamp: datetime) -> float:
    now = datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return (now - timestamp).total_seconds()


def _jitter(
    value: float | int | None,
    fallback: float,
    spread: float,
    low: float,
    high: float,
    digits: int = 1,
) -> float:
    base = fallback if value is None else float(value)
    next_value = max(low, min(high, base + random.uniform(-spread, spread)))
    return round(next_value, digits)


def build_demo_sensor_record(
    device_id: str,
    previous: SensorData | None = None,
) -> SensorData:
    is_risk_demo = device_id.endswith("-002")
    gas_value = 0.8 if is_risk_demo else 0
    mold_low = 2 if is_risk_demo else 0
    mold_high = 3 if is_risk_demo else 1

    return SensorData(
        device_id=device_id,
        temperature=_jitter(previous.temperature if previous else None, 25, 0.35, 22, 31),
        humidity=_jitter(previous.humidity if previous else None, 58, 0.8, 40, 78),
        illuminance=_jitter(previous.illuminance if previous else None, 450, 18, 160, 720, 0),
        aqi=_jitter(previous.aqi if previous else None, 65, 4, 30, 165, 0),
        pm25=_jitter(previous.pm25 if previous else None, 24, 2.5, 8, 92),
        tvoc=_jitter(previous.tvoc if previous else None, 160, 12, 70, 980, 0),
        eco2=_jitter(previous.eco2 if previous else None, 620, 25, 380, 1850, 0),
        mold_risk=round(_jitter(
            previous.mold_risk if previous else None,
            mold_low,
            0.4,
            mold_low,
            mold_high,
            0,
        )),
        gas=gas_value,
        wifi_rssi=round(_jitter(
            previous.wifi_rssi if previous else None,
            -46,
            2,
            -68,
            -34,
            0,
        )),
        focus_mode=previous.focus_mode if previous else False,
        light=previous.light if previous else False,
        light_brightness=previous.light_brightness if previous else 80,
        color_temperature=previous.color_temperature if previous else 3000,
        wechat_notify=previous.wechat_notify if previous else True,
        auto_screen_brightness=previous.auto_screen_brightness if previous else False,
        screen_brightness=previous.screen_brightness if previous else 60,
        timestamp=datetime.now(timezone.utc),
    )
