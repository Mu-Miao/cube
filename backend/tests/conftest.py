# tests/conftest.py
# pytest 测试配置和 fixture

import os
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 - register SQLAlchemy models
from app.api.v1.control import command_queue
from app.config import settings
from app.db.session import Base, get_db
from app.main import app
from app.services.rate_limit import auth_rate_limiter, device_rate_limiter
from app.services.control_queue import control_queue

TEST_DB_PATH = Path(__file__).parent / "test_cube.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"


@pytest.fixture(autouse=True)
def clear_command_queue():
    settings.DEBUG = True
    settings.SECRET_KEY = "test-secret-key-with-at-least-32-characters"
    settings.ALLOW_LEGACY_DEVICE_HANDSHAKE = True
    settings.REDIS_URL = ""
    settings.FIRMWARE_PUBLIC_BASE_URL = "https://tianmuzc.site"
    command_queue.clear()
    control_queue.clear_memory()
    auth_rate_limiter.clear_memory()
    device_rate_limiter.clear_memory()
    yield
    command_queue.clear()
    control_queue.clear_memory()
    auth_rate_limiter.clear_memory()
    device_rate_limiter.clear_memory()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    if TEST_DB_PATH.exists():
        os.remove(TEST_DB_PATH)


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as cleanup_connection:
        for table in reversed(Base.metadata.sorted_tables):
            await cleanup_connection.execute(table.delete())
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session_factory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        async with session_factory() as session:
            yield session
            await session.close()
        await transaction.rollback()
    async with test_engine.begin() as cleanup_connection:
        for table in reversed(Base.metadata.sorted_tables):
            await cleanup_connection.execute(table.delete())


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "password": "test123456",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "test123456",
        },
    )
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
