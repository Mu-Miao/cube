# app/models/base.py
# 所有数据模型的公共基类
# 提供 id 主键和 created_at 创建时间等通用字段

from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class BaseModel(Base):
    """
    所有模型的抽象基类
    自动为每个表提供 id 自增主键和 created_at 创建时间字段
    注意：__abstract__ = True 表示此类不生成对应的数据库表
    """
    __abstract__ = True

    # 自增整数主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 记录创建时间，数据库插入时自动生成
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),  # 使用数据库服务器时间
        nullable=False,
    )
