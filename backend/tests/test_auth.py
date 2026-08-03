# tests/test_auth.py
# 认证模块测试
# 测试用户注册、登录、Token 验证等功能

import pytest
import jwt
from httpx import AsyncClient
from sqlalchemy import select

from app.config import settings
from app.models.refresh_token import RefreshToken
from app.models.user import User


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """正常注册：用户名和密码合法时应返回用户信息"""
    resp = await client.post("/api/v1/auth/register", json={
        "username": "alice",
        "password": "secret123",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["username"] == "alice"


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    """重复注册：相同用户名第二次注册应返回 400"""
    payload = {"username": "bob", "password": "secret123"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_register_strips_username(client: AsyncClient):
    """注册时用户名首尾空格应被清理，避免同一账号出现隐藏差异"""
    resp = await client.post("/api/v1/auth/register", json={
        "username": "  trim_user  ",
        "password": "secret123",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["username"] == "trim_user"


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    """密码过短：少于 8 位的密码应被 Pydantic 校验拒绝"""
    resp = await client.post("/api/v1/auth/register", json={
        "username": "charlie",
        "password": "12",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("password", ["abcdefgh", "12345678"])
async def test_register_requires_letters_and_digits(
    client: AsyncClient,
    password: str,
):
    resp = await client.post("/api/v1/auth/register", json={
        "username": f"weak_{password[0]}",
        "password": password,
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """正常登录：正确的用户名和密码应返回 JWT Token"""
    await client.post("/api/v1/auth/register", json={
        "username": "dave",
        "password": "mypassword1",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": "dave",
        "password": "mypassword1",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert "access_token" in body["data"]
    assert body["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """密码错误：应返回 401"""
    await client.post("/api/v1/auth/register", json={
        "username": "eve",
        "password": "correct123",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": "eve",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_strips_username(client: AsyncClient):
    """登录时用户名首尾空格应被清理，降低移动端输入误差"""
    await client.post("/api/v1/auth/register", json={
        "username": "frank",
        "password": "correct123",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": "  frank  ",
        "password": "correct123",
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_login_invalid_password_hash_returns_401(client: AsyncClient, db_session):
    """数据库中密码哈希损坏时，登录应拒绝而不是抛 500"""
    db_session.add(User(username="broken_hash", password="not-a-bcrypt-hash"))
    await db_session.flush()

    resp = await client.post("/api/v1/auth/login", json={
        "username": "broken_hash",
        "password": "anything",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """用户不存在：应返回 401"""
    resp = await client.post("/api/v1/auth/login", json={
        "username": "nobody",
        "password": "whatever123",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_sets_httponly_refresh_cookie_and_rotates_it(
    client: AsyncClient,
    db_session,
):
    await client.post("/api/v1/auth/register", json={
        "username": "refresh_user",
        "password": "refresh123",
    })
    login = await client.post("/api/v1/auth/login", json={
        "username": "refresh_user",
        "password": "refresh123",
    })
    assert login.status_code == 200
    set_cookie = login.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    assert "path=/api/v1/auth" in set_cookie

    original = client.cookies.get(settings.REFRESH_COOKIE_NAME)
    refreshed = await client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    replacement = client.cookies.get(settings.REFRESH_COOKIE_NAME)
    assert replacement and replacement != original

    user = (
        await db_session.execute(select(User).where(User.username == "refresh_user"))
    ).scalar_one()
    records = (
        await db_session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id)
        )
    ).scalars().all()
    assert len(records) == 2
    assert all(record.token_hash not in {original, replacement} for record in records)
    assert sum(record.revoked_at is not None for record in records) == 1

    replay = await client.post(
        "/api/v1/auth/refresh",
        cookies={settings.REFRESH_COOKIE_NAME: original},
    )
    assert replay.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_cookie(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "username": "logout_user",
        "password": "logout123",
    })
    await client.post("/api/v1/auth/login", json={
        "username": "logout_user",
        "password": "logout123",
    })
    assert client.cookies.get(settings.REFRESH_COOKIE_NAME)
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert client.cookies.get(settings.REFRESH_COOKIE_NAME) is None
    assert (await client.post("/api/v1/auth/refresh")).status_code == 401


@pytest.mark.asyncio
async def test_login_rate_limit_is_five_attempts_per_minute(client: AsyncClient):
    for index in range(5):
        payload = {
            "username": f"limited_user_{index}",
            "password": "bad-password",
        }
        assert (await client.post("/api/v1/auth/login", json=payload)).status_code == 401
    blocked = await client.post("/api/v1/auth/login", json={
        "username": "another_user",
        "password": "bad-password",
    })
    assert blocked.status_code == 429
    assert blocked.headers["retry-after"] == "60"


@pytest.mark.asyncio
async def test_login_failure_lockout_is_per_account_and_success_resets_it(
    client: AsyncClient,
):
    await client.post("/api/v1/auth/register", json={
        "username": "lockout_user",
        "password": "correct123",
    })
    previous_limit = settings.LOGIN_FAILURE_LIMIT
    settings.LOGIN_FAILURE_LIMIT = 2
    try:
        wrong = {"username": "lockout_user", "password": "wrong-password"}
        assert (await client.post("/api/v1/auth/login", json=wrong)).status_code == 401
        assert (await client.post("/api/v1/auth/login", json={
            "username": "lockout_user",
            "password": "correct123",
        })).status_code == 200

        assert (await client.post("/api/v1/auth/login", json=wrong)).status_code == 401
        assert (await client.post("/api/v1/auth/login", json=wrong)).status_code == 401
        blocked = await client.post("/api/v1/auth/login", json=wrong)
        assert blocked.status_code == 429
        assert blocked.headers["retry-after"] == str(settings.LOGIN_LOCKOUT_SECONDS)
    finally:
        settings.LOGIN_FAILURE_LIMIT = previous_limit


@pytest.mark.asyncio
async def test_refresh_requires_trusted_origin_in_production(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "username": "origin_user",
        "password": "origin123",
    })
    await client.post("/api/v1/auth/login", json={
        "username": "origin_user",
        "password": "origin123",
    })

    settings.DEBUG = False
    try:
        rejected = await client.post("/api/v1/auth/refresh")
        assert rejected.status_code == 403
        allowed = await client.post(
            "/api/v1/auth/refresh",
            headers={"Origin": "https://tianmuzc.site"},
        )
        assert allowed.status_code == 200
    finally:
        settings.DEBUG = True


@pytest.mark.asyncio
async def test_register_rate_limit_is_three_attempts_per_minute(client: AsyncClient):
    for index in range(3):
        response = await client.post("/api/v1/auth/register", json={
            "username": f"rate_user_{index}",
            "password": "ratepass123",
        })
        assert response.status_code == 200
    blocked = await client.post("/api/v1/auth/register", json={
        "username": "rate_user_blocked",
        "password": "ratepass123",
    })
    assert blocked.status_code == 429


@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient):
    """未认证访问受保护路由：应返回 403（HTTPBearer 无凭证时默认）"""
    resp = await client.get("/api/v1/device/list")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_protected_route_with_valid_token(client: AsyncClient, auth_headers: dict):
    """携带有效 Token 访问受保护路由：应返回 200"""
    resp = await client.get("/api/v1/device/list", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_protected_route_rejects_token_with_non_integer_user_id(client: AsyncClient):
    """Token 载荷中的 user_id 类型不对时应直接拒绝"""
    token = jwt.encode(
        {"user_id": "1", "username": "bad-token"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    resp = await client.get("/api/v1/device/list", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
