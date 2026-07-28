from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensor_data import SensorData


BOOLEAN_CONTROL_FIELDS = {
    "light",
    "wechat_notify",
    "auto_screen_brightness",
    "focus_mode",
}
INTEGER_CONTROL_FIELDS = {
    "light_brightness",
    "color_temperature",
    "screen_brightness",
}


def normalize_control_status(status: Mapping[str, object] | None) -> dict[str, bool | int]:
    if not status:
        return {}

    normalized: dict[str, bool | int] = {}
    for key in BOOLEAN_CONTROL_FIELDS:
        if key not in status:
            continue
        value = status[key]
        if isinstance(value, bool):
            normalized[key] = value
        elif isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"on", "true", "1"}:
                normalized[key] = True
            elif lowered in {"off", "false", "0"}:
                normalized[key] = False
        elif value is not None:
            normalized[key] = bool(value)

    for key in INTEGER_CONTROL_FIELDS:
        if key not in status:
            continue
        try:
            normalized[key] = int(status[key])
        except (TypeError, ValueError):
            continue

    return normalized


async def persist_latest_control_status(
    db: AsyncSession,
    device_id: str,
    status: Mapping[str, object] | None,
) -> dict[str, bool | int]:
    normalized = normalize_control_status(status)
    if not normalized:
        return {}

    result = await db.execute(
        select(SensorData)
        .where(SensorData.device_id == device_id)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if record:
        for key, value in normalized.items():
            setattr(record, key, value)

    return normalized
