# app/api/v1/auth.py
# 用户认证接口
# 提供：用户注册、登录

from fastapi import APIRouter, Depends, HTTPException
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

router = APIRouter(prefix="/auth", tags=["用户认证"])


@router.post("/register", response_model=ApiResponse[UserInfo])
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    用户注册接口
    POST /api/v1/auth/register

    流程：
    1. 检查用户名是否已存在
    2. 哈希密码并创建新用户
    3. 返回用户基本信息（不含密码）

    错误码：2002 = 用户名已存在
    """
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
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    用户登录接口
    POST /api/v1/auth/login

    流程：
    1. 根据用户名查询用户
    2. 验证密码是否正确
    3. 生成 JWT Token 并返回

    错误码：2003 = 密码错误
    """
    # 查询用户
    user = await get_user_by_username(db, user_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 验证密码
    if not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=401, detail="密码错误")

    # 检查用户是否被禁用
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    # 生成 JWT Token
    access_token = create_access_token({"user_id": user.id, "username": user.username})
    return ApiResponse(
        data=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    )
