# app/main.py
# FastAPI 应用入口文件
# 定义应用实例、注册路由、配置中间件、管理 WebSocket 端点和启动关闭事件

import asyncio
import json

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1 import api_router
from app.config import settings
from app.db.session import init_db
from app.mqtt.client import mqtt_client
from app.mqtt.handlers import handle_mqtt_message
from app.websocket.manager import ws_manager


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
            # 接收客户端消息
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type", "")

            # 兼容两种消息格式：
            #   扁平格式: { type: "auth", token: "xxx" }
            #   嵌套格式: { type: "auth", data: { token: "xxx" } }
            msg_data = msg.get("data", msg)  # 有 data 字段则用嵌套格式，否则整个 msg 即为数据

            if msg_type == "auth":
                # 认证：客户端发送 JWT Token
                token = msg_data.get("token", "") or msg.get("token", "")
                await ws_manager.authenticate(websocket, token)

            elif msg_type == "subscribe":
                # 订阅设备数据推送
                device_id = msg_data.get("device_id", "") or msg.get("device_id", "")
                await ws_manager.subscribe(websocket, device_id)

            elif msg_type == "ping":
                # 心跳保活
                await websocket.send_text(json.dumps({"type": "pong"}))

            else:
                # 未知消息类型，忽略
                pass

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
