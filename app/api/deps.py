# app/api/deps.py
# FastAPI 依赖注入模块
# 定义通用依赖：数据库会话、当前用户认证等

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import decode_access_token, get_user_by_username

# HTTP Bearer Token 认证方案
# 自动从请求头读取 "Authorization: Bearer <token>"
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前认证用户
    作为 Depends() 注入到需要认证的路由中

    流程：
    1. 从请求头提取 Bearer Token
    2. 解码 JWT，提取 user_id
    3. 查询数据库获取用户信息
    4. 验证用户是否处于激活状态

    Raises:
        HTTPException 401: Token 无效、过期或用户不存在
        HTTPException 403: 用户已被禁用
    """
    token = credentials.credentials
    # 解码 JWT Token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
        )
    # 从载荷中获取用户 ID
    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
        )
    # 查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user
