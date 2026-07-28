# app/main.py
# FastAPI 应用入口文件
# 定义应用实例、注册路由、配置中间件、管理 WebSocket 端点和启动关闭事件

import asyncio
import json

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.v1 import api_router
from app.config import BACKEND_DIR, settings
from app.db.session import init_db
from app.mqtt.client import mqtt_client
from app.mqtt.handlers import handle_mqtt_message
from app.websocket.manager import ws_manager
from app.websocket.handlers import handle_ws_message


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器
    启动时：初始化数据库、连接 MQTT、启动后台任务
    关闭时：断开 MQTT 连接、清理资源
    """
    # === 启动阶段 ===
    logger.info(f"正在启动: {settings.APP_NAME}")

    # 初始化数据库（创建表，若已存在则自动跳过）
    await init_db()
    logger.info("数据库初始化完成")

    # 连接 MQTT Broker（如配置了 MQTT）
    asyncio.create_task(mqtt_client.connect(message_handler=handle_mqtt_message))

    async def periodic_cleanup():
        while True:
            await asyncio.sleep(3600)
            try:
                from app.services.cleanup_service import cleanup_old_sensor_data
                await cleanup_old_sensor_data()
            except Exception as e:
                logger.error(f"数据清理失败: {e}")

    asyncio.create_task(periodic_cleanup())

    logger.info(f"启动完成，监听端口 8000")

    yield  # 应用运行期间

    # === 关闭阶段 ===
    logger.info("正在关闭应用...")
    await mqtt_client.disconnect()
    logger.info("应用已关闭")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    description="智能桌面魔方 MVP Demo 后端 API",
    version="2.0.0",
    docs_url="/docs",      # Swagger API 文档
    redoc_url="/redoc",    # ReDoc API 文档
    lifespan=lifespan,
)

# === 注册中间件 ===

# CORS 跨域中间件：允许前端开发服务器跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 允许的前端地址
    allow_credentials=True,               # 允许携带 Cookie
    allow_methods=["*"],                  # 允许所有 HTTP 方法
    allow_headers=["*"],                  # 允许所有请求头
)


# === 注册路由 ===
# 所有 v1 API 路由通过 /api/v1 前缀挂载
app.include_router(api_router)

# OTA 固件静态下载目录。ESP32 收到 OTA 指令后会直接请求这里的 .bin 文件。
FIRMWARE_DIR = BACKEND_DIR / "data" / "firmware"
FIRMWARE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/firmware", StaticFiles(directory=FIRMWARE_DIR), name="firmware")


# === WebSocket 端点 ===

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 连接端点
    前端通过 ws://localhost:8000/ws?token=<JWT> 连接

    连接后流程：
    1. 接受连接
    2. 等待客户端发送认证消息 {type: "auth", token: "JWT"}
    3. 认证成功后处理客户端指令（subscribe、ping 等）
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            await handle_ws_message(websocket, raw)

    except WebSocketDisconnect:
        # 客户端主动断开连接
        ws_manager.disconnect(websocket)
    except Exception:
        # 其他异常（如连接异常断开）
        ws_manager.disconnect(websocket)


# === 健康检查端点 ===

@app.get("/health")
async def health_check():
    """
    健康检查接口
    用于 Docker 健康检查和部署监控
    """
    return {"status": "ok", "app": settings.APP_NAME}
