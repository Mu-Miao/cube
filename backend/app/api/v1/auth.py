# app/api/v1/auth.py
# 用户认证接口
# 提供：用户注册、登录

import hashlib

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.schemas.base import ApiResponse
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserInfo
from app.services.auth_service import (
    register_user,
    get_user_by_username,
    verify_password,
    create_access_token,
)
from app.models.user import User
from app.services.rate_limit import auth_rate_limiter
from app.services.refresh_token_service import (
    issue_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["用户认证"])
AUTH_SCHEME = "bearer"


def _login_failure_key(username: str) -> str:
    digest = hashlib.sha256(username.encode("utf-8")).hexdigest()
    return f"login-account:{digest}"


def _validate_cookie_origin(request: Request) -> None:
    """Require a trusted browser Origin for cookie-authenticated mutations in production."""
    if settings.DEBUG:
        return
    origin = request.headers.get("origin")
    if origin not in settings.CORS_ORIGINS:
        raise HTTPException(status_code=403, detail="不允许的请求来源")


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE or not settings.DEBUG,
        samesite="lax",
        path="/api/v1/auth",
    )


@router.post("/register", response_model=ApiResponse[UserInfo])
async def register(
    user_data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    用户注册接口
    POST /api/v1/auth/register

    流程：
    1. 检查用户名是否已存在
    2. 哈希密码并创建新用户
    3. 返回用户基本信息（不含密码）

    错误码：2002 = 用户名已存在
    """
    client_ip = request.client.host if request.client else "unknown"
    await auth_rate_limiter.check(f"register:{client_ip}", limit=3)

    # 检查用户名是否已存在
    existing = await get_user_by_username(db, user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建新用户
    try:
        new_user = await register_user(db, user_data.username, user_data.password, user_data.email)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在") from None

    return ApiResponse(
        message="注册成功",
        data=UserInfo(id=new_user.id, username=new_user.username, email=new_user.email),
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录接口
    POST /api/v1/auth/login

    流程：
    1. 根据用户名查询用户
    2. 验证密码是否正确
    3. 生成 JWT Token 并返回

    错误码：2003 = 密码错误
    """
    client_ip = request.client.host if request.client else "unknown"
    await auth_rate_limiter.check(
        f"login:{client_ip}",
        limit=5,
    )
    failure_key = _login_failure_key(user_data.username)
    await auth_rate_limiter.check_failures(
        failure_key,
        limit=settings.LOGIN_FAILURE_LIMIT,
        window=settings.LOGIN_LOCKOUT_SECONDS,
    )

    # 查询用户
    user = await get_user_by_username(db, user_data.username)
    if not user:
        await auth_rate_limiter.record_failure(
            failure_key,
            window=settings.LOGIN_LOCKOUT_SECONDS,
        )
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 验证密码
    if not verify_password(user_data.password, user.password):
        await auth_rate_limiter.record_failure(
            failure_key,
            window=settings.LOGIN_LOCKOUT_SECONDS,
        )
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 检查用户是否被禁用
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    await auth_rate_limiter.reset(failure_key)

    # 生成 JWT Token
    access_token = create_access_token({
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
    })
    refresh_token = await issue_refresh_token(db, user.id)
    _set_refresh_cookie(response, refresh_token)
    return ApiResponse(
        data=TokenResponse(
            access_token=access_token,
            token_type=AUTH_SCHEME,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    )


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh_access_token(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
):
    _validate_cookie_origin(request)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="登录已过期")
    rotated = await rotate_refresh_token(db, refresh_token)
    if rotated is None:
        response.delete_cookie(settings.REFRESH_COOKIE_NAME, path="/api/v1/auth")
        raise HTTPException(status_code=401, detail="登录已过期")
    user_id, replacement = rotated
    user = (
        await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    _set_refresh_cookie(response, replacement)
    access_token = create_access_token({
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
    })
    return ApiResponse(data=TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    ))


@router.post("/logout", response_model=ApiResponse)
async def logout(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=settings.REFRESH_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
):
    _validate_cookie_origin(request)
    await revoke_refresh_token(db, refresh_token)
    response.delete_cookie(settings.REFRESH_COOKIE_NAME, path="/api/v1/auth")
    return ApiResponse(message="已退出登录")
