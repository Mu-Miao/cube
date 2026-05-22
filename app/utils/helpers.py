import re
from datetime import datetime, timezone


def validate_device_id(device_id: str) -> bool:
    return bool(re.match(r'^[A-Fa-f0-9]{12}$', device_id))


def validate_mac_address(mac: str) -> bool:
    return bool(re.match(r'^([A-Fa-f0-9]{2}:){5}[A-Fa-f0-9]{2}$', mac))


def format_timestamp(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()


def get_client_ip(request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
