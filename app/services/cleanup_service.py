from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.config import settings
from app.db.session import async_session_factory
from app.models.sensor_data import SensorData
from loguru import logger


async def cleanup_old_sensor_data() -> int:
    retention_days = settings.DATA_RETENTION_DAYS
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    async with async_session_factory() as db:
        result = await db.execute(
            delete(SensorData).where(SensorData.timestamp < cutoff)
        )
        await db.commit()
        deleted = result.rowcount
        if deleted > 0:
            logger.info(f"已清理 {deleted} 条过期传感器数据（>{retention_days}天）")
        return deleted
