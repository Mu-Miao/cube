import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.db.session import async_session_factory, init_db
from app.models.user import User
from app.services.auth_service import hash_password


async def create_admin(username: str, password: str, email: str | None = None):
    await init_db()
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.username == username))
        existing = result.scalar_one_or_none()
        if existing:
            if existing.role == "admin":
                print(f"用户 '{username}' 已经是管理员")
            else:
                existing.role = "admin"
                await db.commit()
                print(f"用户 '{username}' 已升级为管理员")
            return

        user = User(
            username=username,
            password=hash_password(password),
            email=email,
            role="admin",
        )
        db.add(user)
        await db.commit()
        print(f"管理员账号 '{username}' 创建成功")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python create_admin.py <username> <password> [email]")
        sys.exit(1)
    asyncio.run(create_admin(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
