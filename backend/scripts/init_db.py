# scripts/init_db.py
# 数据库初始化脚本
# 首次运行时执行，创建数据库表并初始化默认数据
# 使用方法: python scripts/init_db.py

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径，以便导入 app 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import init_db, engine
from loguru import logger


async def main():
    """
    初始化数据库：
    1. 创建所有定义的数据表（users, devices, sensor_data）
    2. 若表已存在则自动跳过，不会覆盖已有数据
    """
    logger.info("开始初始化数据库...")
    await init_db()
    logger.info("数据库表创建完成")

    # 关闭数据库引擎
    await engine.dispose()
    logger.info("数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
