import argparse
import asyncio
import math
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import async_session_factory, engine, init_db
from app.models.device import Device
from app.models.operation_log import OperationLog
from app.models.sensor_data import SensorData
from app.models.user import User
from app.models.voice_log import VoiceLog
from app.services.auth_service import hash_password


DEMO_USER = "demo"
DEMO_ADMIN = "admin"
DEMO_PASSWORD = "demo123456"


@dataclass(frozen=True)
class DemoDevice:
    device_id: str
    name: str
    status: str
    chip_model: str = "ESP32-S3"
    firmware_version: str = "v1.0.0-demo"


DEMO_DEVICES = [
    DemoDevice("DEMO-CUBE-001", "魔方终端-客厅", "online"),
    DemoDevice("DEMO-CUBE-002", "魔方终端-书桌", "online"),
    DemoDevice("DEMO-CUBE-003", "魔方终端-卧室", "offline"),
]


async def _column_exists(db: AsyncSession, table_name: str, column_name: str) -> bool:
    result = await db.execute(text(f"PRAGMA table_info({table_name})"))
    return any(row[1] == column_name for row in result.fetchall())


async def _add_column_if_missing(
    db: AsyncSession,
    table_name: str,
    column_name: str,
    definition: str,
) -> None:
    if not await _column_exists(db, table_name, column_name):
        await db.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"))


async def ensure_demo_schema(db: AsyncSession) -> None:
    """补齐旧版 SQLite 演示库中缺失的新增字段。"""
    await _add_column_if_missing(db, "users", "email", "VARCHAR(100)")
    await _add_column_if_missing(db, "users", "is_active", "BOOLEAN DEFAULT 1")
    await _add_column_if_missing(db, "users", "role", "VARCHAR(20) DEFAULT 'user' NOT NULL")

    await _add_column_if_missing(db, "devices", "token", "VARCHAR(128)")
    await _add_column_if_missing(db, "devices", "status", "VARCHAR(20) DEFAULT 'offline' NOT NULL")
    await _add_column_if_missing(db, "devices", "chip_model", "VARCHAR(50)")
    await _add_column_if_missing(db, "devices", "firmware_version", "VARCHAR(20)")
    await _add_column_if_missing(db, "devices", "bound_user_id", "INTEGER")
    await _add_column_if_missing(db, "devices", "last_seen", "DATETIME")

    await _add_column_if_missing(db, "sensor_data", "illuminance", "DOUBLE")
    await _add_column_if_missing(db, "sensor_data", "aqi", "DOUBLE")
    await _add_column_if_missing(db, "sensor_data", "pm25", "DOUBLE")
    await _add_column_if_missing(db, "sensor_data", "tvoc", "DOUBLE")
    await _add_column_if_missing(db, "sensor_data", "eco2", "DOUBLE")
    await _add_column_if_missing(db, "sensor_data", "mold_risk", "DOUBLE")
    await _add_column_if_missing(db, "sensor_data", "gas", "DOUBLE")
    await _add_column_if_missing(db, "sensor_data", "wifi_rssi", "INTEGER")
    await _add_column_if_missing(db, "sensor_data", "focus_mode", "INTEGER")
    await db.commit()


async def _upsert_user(
    db: AsyncSession,
    username: str,
    password: str,
    role: str,
    email: str | None = None,
) -> User:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            username=username,
            password=hash_password(password),
            role=role,
            email=email,
            is_active=True,
        )
        db.add(user)
        await db.flush()
    else:
        user.password = hash_password(password)
        user.role = role
        user.email = email or user.email
        user.is_active = True
    return user


async def _upsert_device(
    db: AsyncSession,
    demo_device: DemoDevice,
    owner_id: int,
    now: datetime,
) -> Device:
    result = await db.execute(select(Device).where(Device.device_id == demo_device.device_id))
    device = result.scalar_one_or_none()
    last_seen = now if demo_device.status == "online" else now - timedelta(hours=3)
    token = f"dev_demo_{demo_device.device_id.lower().replace('-', '_')}"

    if device is None:
        device = Device(device_id=demo_device.device_id)
        db.add(device)
        await db.flush()

    device.device_name = demo_device.name
    device.status = demo_device.status
    device.token = token
    device.chip_model = demo_device.chip_model
    device.firmware_version = demo_device.firmware_version
    device.bound_user_id = owner_id
    device.last_seen = last_seen
    return device


def _normal_record(device_id: str, timestamp: datetime, index: int) -> SensorData:
    daily_wave = math.sin(index / 5)
    return SensorData(
        device_id=device_id,
        temperature=round(24.2 + daily_wave * 2.1, 1),
        humidity=round(52 + math.cos(index / 6) * 8, 1),
        illuminance=round(420 + max(0, math.sin(index / 4)) * 260, 1),
        aqi=round(38 + max(0, math.sin(index / 7)) * 30, 1),
        pm25=round(12 + max(0, math.sin(index / 7)) * 18, 1),
        tvoc=round(120 + max(0, math.sin(index / 8)) * 90, 1),
        eco2=round(520 + max(0, math.sin(index / 6)) * 180, 1),
        mold_risk=0 if index % 9 else 1,
        gas=0,
        wifi_rssi=-42 - (index % 8),
        focus_mode=index % 11 == 0,
        timestamp=timestamp,
    )


def _risk_record(device_id: str, timestamp: datetime, index: int) -> SensorData:
    pressure = max(0, math.sin(index / 3))
    is_latest_window = timestamp >= datetime.now(timezone.utc) - timedelta(hours=2)
    return SensorData(
        device_id=device_id,
        temperature=round(27.8 + pressure * 2.5, 1),
        humidity=round(66 + pressure * 10, 1),
        illuminance=round(240 + pressure * 130, 1),
        aqi=round(95 + pressure * 70, 1),
        pm25=round(36 + pressure * 54, 1),
        tvoc=round(460 + pressure * 520, 1),
        eco2=round(950 + pressure * 900, 1),
        mold_risk=3 if is_latest_window else 2,
        gas=0.8 if is_latest_window else 0,
        wifi_rssi=-55 - (index % 9),
        focus_mode=False,
        timestamp=timestamp,
    )


def _offline_record(device_id: str, timestamp: datetime, index: int) -> SensorData:
    return SensorData(
        device_id=device_id,
        temperature=round(22.4 + math.sin(index / 5) * 1.4, 1),
        humidity=round(45 + math.cos(index / 6) * 4, 1),
        illuminance=180,
        aqi=55,
        pm25=18,
        tvoc=180,
        eco2=620,
        mold_risk=1,
        gas=0,
        wifi_rssi=-70,
        focus_mode=False,
        timestamp=timestamp,
    )


async def _refresh_sensor_data(db: AsyncSession, now: datetime) -> int:
    device_ids = [device.device_id for device in DEMO_DEVICES]
    await db.execute(delete(SensorData).where(SensorData.device_id.in_(device_ids)))

    rows: list[SensorData] = []
    start = now - timedelta(days=7)
    for index in range(7 * 24):
        timestamp = start + timedelta(hours=index)
        rows.append(_normal_record("DEMO-CUBE-001", timestamp, index))
        rows.append(_risk_record("DEMO-CUBE-002", timestamp, index))
        if index < 7 * 24 - 4:
            rows.append(_offline_record("DEMO-CUBE-003", timestamp, index))

    for minute_index in range(24):
        timestamp = now - timedelta(minutes=(24 - minute_index) * 5)
        rows.append(_normal_record("DEMO-CUBE-001", timestamp, 200 + minute_index))
        rows.append(_risk_record("DEMO-CUBE-002", timestamp, 200 + minute_index))

    db.add_all(rows)
    return len(rows)


async def _refresh_logs(db: AsyncSession, user_id: int, now: datetime) -> tuple[int, int]:
    device_ids = [device.device_id for device in DEMO_DEVICES]
    await db.execute(delete(OperationLog).where(OperationLog.device_id.in_(device_ids)))
    await db.execute(delete(VoiceLog).where(VoiceLog.device_id.in_(device_ids)))

    operation_logs = [
        OperationLog(
            user_id=user_id,
            device_id="DEMO-CUBE-001",
            action="bind_device",
            detail="绑定演示设备：魔方终端-客厅",
            ip_address="127.0.0.1",
            created_at=now - timedelta(hours=5),
        ),
        OperationLog(
            user_id=user_id,
            device_id="DEMO-CUBE-001",
            action="control",
            detail="灯光切换为开启，亮度 80%",
            ip_address="127.0.0.1",
            created_at=now - timedelta(minutes=38),
        ),
        OperationLog(
            user_id=user_id,
            device_id="DEMO-CUBE-002",
            action="alert",
            detail="检测到燃气、CO2、霉菌风险，请立即通风",
            ip_address="127.0.0.1",
            created_at=now - timedelta(minutes=12),
        ),
        OperationLog(
            user_id=user_id,
            device_id="DEMO-CUBE-003",
            action="device_offline",
            detail="设备超过 90 秒未心跳，已标记离线",
            ip_address="127.0.0.1",
            created_at=now - timedelta(hours=3),
        ),
    ]

    voice_logs = [
        VoiceLog(
            user_id=user_id,
            device_id="DEMO-CUBE-001",
            command_text="打开客厅魔方灯光",
            intent="light_on",
            executed=True,
            response_text="已打开客厅灯光",
            created_at=now - timedelta(minutes=35),
        ),
        VoiceLog(
            user_id=user_id,
            device_id="DEMO-CUBE-002",
            command_text="现在空气质量怎么样",
            intent="query_air_quality",
            executed=True,
            response_text="当前空气质量偏差，建议立即通风",
            created_at=now - timedelta(minutes=10),
        ),
    ]

    db.add_all(operation_logs + voice_logs)
    return len(operation_logs), len(voice_logs)


async def seed_demo_data(db: AsyncSession) -> dict[str, int | str]:
    await ensure_demo_schema(db)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    demo_user = await _upsert_user(
        db,
        DEMO_USER,
        DEMO_PASSWORD,
        "user",
        "demo@example.com",
    )
    demo_admin = await _upsert_user(
        db,
        DEMO_ADMIN,
        DEMO_PASSWORD,
        "admin",
        "admin@example.com",
    )
    await db.flush()

    for demo_device in DEMO_DEVICES:
        await _upsert_device(db, demo_device, demo_user.id, now)

    sensor_count = await _refresh_sensor_data(db, now)
    operation_count, voice_count = await _refresh_logs(db, demo_user.id, now)
    await db.commit()

    return {
        "demo_user": DEMO_USER,
        "demo_admin": DEMO_ADMIN,
        "password": DEMO_PASSWORD,
        "devices": len(DEMO_DEVICES),
        "sensor_rows": sensor_count,
        "operation_logs": operation_count,
        "voice_logs": voice_count,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="生成智能桌面魔方演示数据")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="跳过交互确认，直接刷新演示数据",
    )
    args = parser.parse_args()

    if not args.yes:
        answer = input(
            "将创建/更新 demo、admin 账号，并刷新 DEMO-CUBE-* 演示数据。继续？[y/N] "
        )
        if answer.lower() not in {"y", "yes"}:
            print("已取消")
            return

    await init_db()
    async with async_session_factory() as db:
        summary = await seed_demo_data(db)

    await engine.dispose()
    print("演示数据已准备完成")
    print(f"普通账号: {summary['demo_user']} / {summary['password']}")
    print(f"管理员账号: {summary['demo_admin']} / {summary['password']}")
    print(f"设备数量: {summary['devices']}")
    print(f"传感器数据: {summary['sensor_rows']} 条")
    print(f"操作日志: {summary['operation_logs']} 条")
    print(f"语音日志: {summary['voice_logs']} 条")


if __name__ == "__main__":
    asyncio.run(main())
