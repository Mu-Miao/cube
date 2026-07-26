from datetime import datetime, timedelta, timezone


SHANGHAI_TIMEZONE = timezone(timedelta(hours=8), name="Asia/Shanghai")


def to_shanghai_time(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(SHANGHAI_TIMEZONE)


def shanghai_isoformat(value: datetime | None) -> str | None:
    converted = to_shanghai_time(value)
    return converted.isoformat() if converted else None


def format_shanghai_time(
    value: datetime | None,
    format_string: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    converted = to_shanghai_time(value)
    return converted.strftime(format_string) if converted else ""
