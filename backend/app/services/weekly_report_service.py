from datetime import datetime, timedelta, timezone

from sqlalchemy import Date, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensor_data import SensorData


async def aggregate_weekly_days(
    db: AsyncSession,
    device_id: str,
) -> list[dict]:
    """Aggregate seven days in SQL instead of loading every sensor row."""
    dialect = db.bind.dialect.name
    if dialect == "postgresql":
        local_day = cast(
            SensorData.timestamp + text("INTERVAL '8 hours'"),
            Date,
        )
    else:
        local_day = func.date(func.datetime(SensorData.timestamp, "+8 hours"))

    rows = (
        await db.execute(
            select(
                local_day.label("day"),
                func.avg(SensorData.temperature).label("temperature"),
                func.avg(SensorData.humidity).label("humidity"),
                func.avg(SensorData.aqi).label("aqi"),
                func.count(SensorData.id).label("sample_count"),
            )
            .where(
                SensorData.device_id == device_id,
                SensorData.timestamp >= datetime.now(timezone.utc) - timedelta(days=7),
            )
            .group_by(local_day)
            .order_by(local_day)
        )
    ).all()
    return [
        {
            "date": row.day.isoformat() if hasattr(row.day, "isoformat") else str(row.day),
            "temperature": round(row.temperature, 1) if row.temperature is not None else None,
            "humidity": round(row.humidity, 1) if row.humidity is not None else None,
            "aqi": round(row.aqi, 1) if row.aqi is not None else None,
            "sample_count": row.sample_count,
        }
        for row in rows
    ]
