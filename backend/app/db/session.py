# app/db/session.py
# 异步数据库会话管理
# 配置 SQLAlchemy 异步引擎和会话工厂，提供 get_db 依赖注入

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# 将相对路径的数据库 URL 转为基于项目根目录的绝对路径，避免 CWD 影响路径解析
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if settings.DATABASE_URL.startswith("sqlite"):
    raw_db_path = settings.DATABASE_URL.split("///")[-1]
    db_path = Path(raw_db_path)
    if not db_path.is_absolute():
        db_path = _PROJECT_ROOT / db_path
        settings.DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"
    db_path.parent.mkdir(parents=True, exist_ok=True)

# 创建异步数据库引擎
# 使用 aiosqlite 驱动实现 SQLite 的异步操作
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 调试模式下打印 SQL 语句
    future=True,  # 使用 SQLAlchemy 2.0 风格 API
)


if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine.sync_engine, "connect")
    def _configure_sqlite(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

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

    if not settings.DEBUG:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def verify_database_migration() -> None:
    """Refuse production startup when the database is not at Alembic head."""
    config = Config(str(_PROJECT_ROOT / "alembic.ini"))
    expected_revision = ScriptDirectory.from_config(config).get_current_head()
    async with engine.connect() as connection:
        current_revision = (
            await connection.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one_or_none()
    if not expected_revision or current_revision != expected_revision:
        raise RuntimeError(
            "数据库迁移版本不匹配，"
            f"current={current_revision or 'none'} expected={expected_revision or 'none'}；"
            "请先执行 alembic upgrade head"
        )
