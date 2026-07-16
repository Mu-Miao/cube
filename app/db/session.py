# app/db/session.py
# 异步数据库会话管理
# 配置 SQLAlchemy 异步引擎和会话工厂，提供 get_db 依赖注入

import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# 将相对路径的数据库 URL 转为基于项目根目录的绝对路径，避免 CWD 影响路径解析
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_raw_db_path = settings.DATABASE_URL.split("///")[-1]
if not os.path.isabs(_raw_db_path):
    _abs_db_path = _PROJECT_ROOT / _raw_db_path
    settings.DATABASE_URL = f"sqlite+aiosqlite:///{_abs_db_path}"
    _db_dir = str(_abs_db_path.parent)
else:
    _db_dir = os.path.dirname(_raw_db_path)

# 确保数据库文件所在目录存在（SQLite 异步版不会自动创建目录）
if _db_dir:
    Path(_db_dir).mkdir(parents=True, exist_ok=True)

# 创建异步数据库引擎
# 使用 aiosqlite 驱动实现 SQLite 的异步操作
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 调试模式下打印 SQL 语句
    future=True,  # 使用 SQLAlchemy 2.0 风格 API
)

# 创建异步会话工厂
# 每次数据库操作通过此工厂获取独立的会话
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不使属性过期，避免意外懒加载
)


class Base(DeclarativeBase):
    """
    所有数据模型的基类
    继承 DeclarativeBase 以支持 SQLAlchemy 2.0 ORM 声明
    """
    pass


async def get_db() -> AsyncSession:
    """
    获取数据库会话的依赖函数
    用于 FastAPI 的 Depends() 注入，自动管理会话的创建和关闭
    确保每次请求使用独立的数据库会话，异常时自动回滚
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()  # 正常结束时自动提交
        except Exception:
            await session.rollback()  # 异常时回滚
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库：创建所有定义的数据表
    仅创建 Base 元数据中注册的表，不会影响已有数据
    首次运行时调用，后续启动自动跳过已存在的表
    """
    # 导入模型，确保表注册到 Base.metadata
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.DATABASE_URL.startswith("sqlite"):
            columns = await conn.execute(text("PRAGMA table_info(sensor_data)"))
            column_names = {row[1] for row in columns}
            if "pm25" not in column_names:
                await conn.execute(text("ALTER TABLE sensor_data ADD COLUMN pm25 DOUBLE"))
