"""Copy an existing Cube SQLite database into an empty migrated PostgreSQL database."""

import argparse
import asyncio
import hashlib
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import MetaData, func, insert, select, text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.models  # noqa: F401
from app.config import settings
from app.db.session import Base


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将 Cube SQLite 数据复制到已执行 Alembic upgrade head 的空 PostgreSQL",
    )
    parser.add_argument(
        "--sqlite-url",
        default="sqlite+aiosqlite:///./data/cube.db",
        help="源 SQLite 异步 SQLAlchemy URL",
    )
    parser.add_argument(
        "--postgres-url",
        default=os.getenv("POSTGRES_DATABASE_URL", ""),
        help="目标 PostgreSQL asyncpg URL，也可设置 POSTGRES_DATABASE_URL",
    )
    parser.add_argument("--batch-size", type=int, default=500)
    return parser.parse_args()


def _normalize_device_row(row: dict) -> dict:
    token = row.get("token")
    if token and not str(token).startswith("sha256$"):
        row["token"] = "sha256$" + hashlib.sha256(str(token).encode()).hexdigest()
        row["token_expires_at"] = datetime.now(timezone.utc) + timedelta(
            seconds=settings.DEVICE_TOKEN_EXPIRE_SECONDS
        )
    return row


async def migrate(sqlite_url: str, postgres_url: str, batch_size: int) -> dict[str, int]:
    if not sqlite_url.startswith("sqlite+aiosqlite:"):
        raise ValueError("--sqlite-url 必须使用 sqlite+aiosqlite")
    if not postgres_url.startswith(("postgresql+asyncpg:", "postgres+asyncpg:")):
        raise ValueError("--postgres-url 必须使用 postgresql+asyncpg")
    if batch_size < 1:
        raise ValueError("--batch-size 必须大于 0")

    source_engine = create_async_engine(sqlite_url)
    target_engine = create_async_engine(postgres_url)
    source_metadata = MetaData()
    counts: dict[str, int] = {}
    try:
        async with source_engine.connect() as source:
            await source.run_sync(source_metadata.reflect)
            async with target_engine.begin() as target:
                target_tables = set(
                    await target.run_sync(
                        lambda connection: set(
                            __import__("sqlalchemy").inspect(connection).get_table_names()
                        )
                    )
                )
                missing = {
                    table.name for table in Base.metadata.sorted_tables
                    if table.name not in target_tables
                }
                if missing:
                    raise RuntimeError(
                        "目标库尚未完成 Alembic 迁移，缺少表: " + ", ".join(sorted(missing))
                    )

                for target_table in Base.metadata.sorted_tables:
                    source_table = source_metadata.tables.get(target_table.name)
                    if source_table is None:
                        counts[target_table.name] = 0
                        continue
                    target_count = (
                        await target.execute(select(func.count()).select_from(target_table))
                    ).scalar_one()
                    if target_count:
                        raise RuntimeError(
                            f"目标表 {target_table.name} 非空（{target_count} 条），已停止以避免重复数据"
                        )

                    rows = (await source.execute(select(source_table))).mappings().all()
                    allowed = set(target_table.c.keys())
                    payloads = [
                        {key: value for key, value in dict(row).items() if key in allowed}
                        for row in rows
                    ]
                    if target_table.name == "devices":
                        payloads = [_normalize_device_row(row) for row in payloads]
                    for offset in range(0, len(payloads), batch_size):
                        await target.execute(
                            insert(target_table),
                            payloads[offset:offset + batch_size],
                        )
                    counts[target_table.name] = len(payloads)

                for table in Base.metadata.sorted_tables:
                    if "id" not in table.c or counts.get(table.name, 0) == 0:
                        continue
                    await target.execute(text(
                        "SELECT setval(pg_get_serial_sequence(:table_name, 'id'), "
                        f"(SELECT MAX(id) FROM {table.name}), true)"
                    ), {"table_name": table.name})

                for table in Base.metadata.sorted_tables:
                    actual = (
                        await target.execute(select(func.count()).select_from(table))
                    ).scalar_one()
                    if actual != counts.get(table.name, 0):
                        raise RuntimeError(
                            f"条数校验失败: {table.name} source={counts.get(table.name, 0)} "
                            f"target={actual}"
                        )
    finally:
        await source_engine.dispose()
        await target_engine.dispose()
    return counts


async def _main() -> None:
    args = _arguments()
    counts = await migrate(args.sqlite_url, args.postgres_url, args.batch_size)
    for table_name, count in counts.items():
        print(f"{table_name}: {count}")
    print(f"迁移与条数校验完成，共 {sum(counts.values())} 条")


if __name__ == "__main__":
    asyncio.run(_main())
