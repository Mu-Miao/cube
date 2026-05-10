# app/models/user.py
# 用户模型 - users 表
# 定义用户表结构：用户名、密码哈希、邮箱、状态等
# MVP 版本移除了 role 字段（不实现管理员功能）

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    """
    用户数据模型 - users 表
    用于存储注册用户信息，支持设备绑定关联
    """
    __tablename__ = "users"

    # 用户名，50 字符以内，全局唯一，注册时必填
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # 密码哈希值，使用 bcrypt 加密存储，不存储明文密码
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    # 邮箱地址，可选字段，100 字符以内，如果填写则需唯一
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)

    # 账号是否启用，默认启用，可用于后续封禁功能扩展
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
