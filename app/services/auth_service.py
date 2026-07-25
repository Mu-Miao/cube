# app/services/auth_service.py
# 认证服务
# 处理用户注册、登录、JWT Token 生成与验证、密码加密等业务逻辑

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User


def hash_password(password: str) -> str:
    """
    对明文密码进行 bcrypt 哈希
    注册时使用，存储到数据库的 password 字段
    bcrypt 5.x 会自动生成并包含 salt
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与哈希密码匹配
    登录时使用，比较用户输入密码与数据库存储的哈希值
    """
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except ValueError:
        logger.warning("用户密码哈希格式无效，已拒绝本次登录")
        return False


def create_access_token(data: dict) -> str:
    """
    生成 JWT 访问令牌
    登录成功后调用，返回给前端存储

    Args:
        data: 要编码到 Token 中的载荷（如 user_id, username）
    Returns:
        编码后的 JWT 字符串
    """
    to_encode = data.copy()
    # 计算 Token 过期时间
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # 使用配置中的密钥和算法签名 Token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码并验证 JWT 令牌
    用于验证请求中的 Token 是否有效

    Args:
        token: JWT 字符串
    Returns:
        解码后的载荷字典（含 user_id 等），无效或过期返回 None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    根据用户名查询用户
    注册时用于检查用户名是否已存在
    登录时用于查询用户信息进行密码验证

    Args:
        db: 数据库会话
        username: 用户名
    Returns:
        User 对象或 None
    """
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, username: str, password: str, email: str | None = None) -> User:
    """
    注册新用户
    创建用户记录并将密码哈希后存储

    Args:
        db: 数据库会话
        username: 用户名
        password: 明文密码（将被哈希）
        email: 邮箱（可选）
    Returns:
        新创建的 User 对象
    """
    user = User(
        username=username,
        password=hash_password(password),
        email=email,
    )
    db.add(user)
    await db.flush()  # 刷新以获取自增 id
    await db.refresh(user)
    return user
