# app/schemas/user.py
# 用户相关 Pydantic 模型
# 定义用户注册、登录、响应等数据校验模型

from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _strip_text(value: str) -> str:
    return value.strip()


class UserRegister(BaseModel):
    """
    用户注册请求体
    POST /api/v1/auth/register
    校验用户名长度、密码强度和邮箱格式
    """
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码（最少6位）")
    email: Optional[str] = Field(None, max_length=100, description="邮箱（可选）")

    _normalize_username = field_validator("username")(_strip_text)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class UserLogin(BaseModel):
    """
    用户登录请求体
    POST /api/v1/auth/login
    """
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, max_length=128, description="密码")

    _normalize_username = field_validator("username")(_strip_text)


class TokenResponse(BaseModel):
    """
    登录成功返回的 Token 信息
    """
    access_token: str  # JWT 访问令牌
    token_type: str = "bearer"  # Token 类型，固定为 bearer
    expires_in: int  # Token 有效期（秒）


class UserInfo(BaseModel):
    """
    用户基本信息（不含密码）
    用于注册成功后返回用户数据
    """
    id: int  # 用户 ID
    username: str  # 用户名
    email: Optional[str] = None  # 邮箱
    role: str = "user"

    class Config:
        from_attributes = True  # 支持从 SQLAlchemy 模型转换
