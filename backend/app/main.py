# app/main.py
# FastAPI 应用入口文件
# 定义应用实例、注册路由、配置中间件、管理 WebSocket 端点和启动关闭事件

import asyncio
import json

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy import text

from app.api.v1 import api_router
from app.config import settings, validate_runtime_settings
from app.db.session import async_session_factory, init_db, verify_database_migration
from app.mqtt.client import mqtt_client
from app.mqtt.handlers import handle_mqtt_message
from app.services.device_service import refresh_all_stale_device_statuses
from app.services.redis_event_bus import redis_event_bus
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
    validate_runtime_settings()
    app.state.cleanup_failures = 0
    app.state.cleanup_last_error = None

    if settings.DEBUG:
        await init_db()
        logger.info("开发数据库初始化完成")
    else:
        await verify_database_migration()
        logger.info("生产数据库 Alembic 版本校验通过")

    # 连接 MQTT Broker（如配置了 MQTT）
    asyncio.create_task(mqtt_client.connect(message_handler=handle_mqtt_message))

    async def periodic_cleanup():
        retry_delay = 3600
        while True:
            await asyncio.sleep(retry_delay)
            try:
                from app.services.cleanup_service import cleanup_old_sensor_data
                await cleanup_old_sensor_data()
                app.state.cleanup_failures = 0
                app.state.cleanup_last_error = None
                retry_delay = 3600
            except Exception as e:
                app.state.cleanup_failures += 1
                app.state.cleanup_last_error = type(e).__name__
                retry_delay = min(
                    3600,
                    60 * (2 ** min(app.state.cleanup_failures - 1, 6)),
                )
                logger.error(
                    "数据清理失败（连续 {} 次，{} 秒后重试）: {}",
                    app.state.cleanup_failures,
                    retry_delay,
                    e,
                )

    cleanup_task = asyncio.create_task(periodic_cleanup())

    async def periodic_device_status_refresh():
        interval = max(5, min(30, settings.DEVICE_HEARTBEAT_TIMEOUT_SECONDS // 3))
        while True:
            await asyncio.sleep(interval)
            try:
                async with async_session_factory() as db:
                    stale_device_ids = await refresh_all_stale_device_statuses(db)
                    await db.commit()
                for device_id in stale_device_ids:
                    await ws_manager.broadcast_device_status(device_id, "offline")
            except Exception as e:
                logger.error(f"设备离线状态刷新失败: {e}")

    device_status_task = asyncio.create_task(periodic_device_status_refresh())
    redis_listener_task = asyncio.create_task(
        redis_event_bus.listen(ws_manager.broadcast_external)
    )

    logger.info(f"启动完成，监听端口 8000")

    yield  # 应用运行期间

    # === 关闭阶段 ===
    logger.info("正在关闭应用...")
    for task in (cleanup_task, device_status_task):
        task.cancel()
    await redis_event_bus.close()
    redis_listener_task.cancel()
    await asyncio.gather(
        cleanup_task,
        device_status_task,
        redis_listener_task,
        return_exceptions=True,
    )
    await mqtt_client.disconnect()
    logger.info("应用已关闭")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    description="智能桌面魔方 MVP Demo 后端 API",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# === 注册中间件 ===

# CORS 跨域中间件：允许前端开发服务器跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 允许的前端地址
    allow_credentials=True,               # 允许携带 Cookie
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


# === 注册路由 ===
# 所有 v1 API 路由通过 /api/v1 前缀挂载
app.include_router(api_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "未处理的服务端异常: method={} path={}",
        request.method,
        request.url.path,
    )
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})

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
    if not await ws_manager.connect(websocket):
        return
    try:
        while True:
            raw = await asyncio.wait_for(
                websocket.receive_text(),
                timeout=settings.WS_PING_INTERVAL * 2,
            )
            await handle_ws_message(websocket, raw)

    except TimeoutError:
        await websocket.close(code=1001, reason="心跳超时")
        ws_manager.disconnect(websocket)
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
    components: dict[str, str] = {}
    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
        components["database"] = "ok"
    except Exception:
        components["database"] = "error"

    if settings.REDIS_URL:
        try:
            components["redis"] = "ok" if await redis_event_bus.ping() else "error"
        except Exception:
            components["redis"] = "error"
        components["redis_listener"] = (
            "ok" if redis_event_bus.connected else "reconnecting"
        )
    else:
        components["redis"] = "disabled"
        components["redis_listener"] = "disabled"

    components["mqtt"] = "ok" if mqtt_client.is_connected else "disabled"
    cleanup_failures = getattr(app.state, "cleanup_failures", 0)
    components["cleanup"] = "ok" if cleanup_failures == 0 else "degraded"
    healthy = components["database"] == "ok" and (
        settings.DEBUG
        or (
            components["redis"] == "ok"
            and components["redis_listener"] == "ok"
            and components["mqtt"] == "ok"
            and components["cleanup"] == "ok"
        )
    )
    payload = {
        "status": "ok" if healthy else "degraded",
        "app": settings.APP_NAME,
        "components": components,
        "cleanup_failures": cleanup_failures,
        "redis_listener_failures": redis_event_bus.failure_count,
        "redis_listener_last_error": redis_event_bus.last_error,
    }
    return JSONResponse(status_code=200 if healthy else 503, content=payload)
