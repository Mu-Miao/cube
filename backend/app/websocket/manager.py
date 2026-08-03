# app/websocket/manager.py
# WebSocket 连接管理器
# 管理所有活跃的 WebSocket 连接、用户认证、设备订阅、消息广播

import asyncio
import json
import time
from typing import Any

from fastapi import WebSocket

from app.config import settings
from app.services.auth_service import decode_access_token
from app.services.redis_event_bus import redis_event_bus


class WebSocketManager:
    """
    WebSocket 连接管理器（单例模式）
    维护所有活跃的 WebSocket 连接，支持：
      - 用户认证（连接时发送 JWT Token）
      - 设备订阅（用户订阅特定设备的数据推送）
      - 消息广播（向订阅某设备的所有客户端推送数据）
      - 心跳保活（ping/pong）
    """

    def __init__(self):
        # 所有活跃连接：{websocket: {"user_id": int, "device_ids": set()}}
        self.active_connections: dict[WebSocket, dict[str, Any]] = {}
        self._connect_lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> bool:
        """
        接受 WebSocket 连接
        连接建立后客户端需发送认证消息
        """
        async with self._connect_lock:
            if len(self.active_connections) >= settings.WS_MAX_CONNECTIONS:
                await websocket.close(code=1013, reason="连接数已达上限")
                return False
            unauthenticated_count = sum(
                info["user_id"] is None
                for info in self.active_connections.values()
            )
            if unauthenticated_count >= settings.WS_MAX_UNAUTHENTICATED_CONNECTIONS:
                await websocket.close(code=1013, reason="待认证连接数已达上限")
                return False
            await websocket.accept()
            self.active_connections[websocket] = {
                "user_id": None,
                "device_ids": set(),
            }
        return True

    def disconnect(self, websocket: WebSocket) -> None:
        """
        断开 WebSocket 连接，清理相关资源
        """
        self.active_connections.pop(websocket, None)

    def get_authenticated_user_id(self, websocket: WebSocket) -> int | None:
        connection = self.active_connections.get(websocket)
        if not connection:
            return None
        user_id = connection.get("user_id")
        return user_id if isinstance(user_id, int) else None

    async def authenticate(self, websocket: WebSocket, token: str) -> bool:
        """
        验证客户端 JWT Token
        认证成功则绑定 user_id 到连接，返回 True
        认证失败则发送错误消息并返回 False
        """
        payload = decode_access_token(token)
        if payload is None:
            await websocket.send_text(json.dumps({
                "type": "auth_result",
                "code": 1001,
                "message": "无效的认证凭证",
            }))
            return False

        user_id = payload.get("user_id")
        if user_id is None:
            await websocket.send_text(json.dumps({
                "type": "auth_result",
                "code": 1001,
                "message": "无效的认证凭证",
            }))
            return False

        # 认证成功，绑定用户 ID
        self.active_connections[websocket]["user_id"] = user_id
        await websocket.send_text(json.dumps({
            "type": "auth_result",
            "code": 0,
            "message": "ok",
        }))
        return True

    async def send_subscribe_result(
        self,
        websocket: WebSocket,
        code: int,
        message: str,
    ) -> None:
        await websocket.send_text(json.dumps({
            "type": "subscribe_result",
            "code": code,
            "message": message,
        }))

    async def subscribe(self, websocket: WebSocket, device_id: str) -> None:
        """
        客户端订阅设备数据推送
        订阅后该设备的所有传感器数据都会推送给此客户端
        """
        connection = self.active_connections.get(websocket)
        if not connection or self.get_authenticated_user_id(websocket) is None:
            await self.send_subscribe_result(websocket, 1002, "请先完成认证")
            return

        connection["device_ids"].add(device_id)
        await self.send_subscribe_result(websocket, 0, "ok")

    async def broadcast_sensor_data(self, device_id: str, data: dict) -> None:
        """
        向所有订阅了某设备的客户端广播传感器数据
        当设备上报数据时调用此方法
        """
        message = json.dumps({
            "type": "sensor_data",
            "data": {"device_id": device_id, **data},
            "timestamp": int(time.time() * 1000),
        })
        await self._broadcast(device_id, message)

    async def broadcast_device_status(self, device_id: str, status: str) -> None:
        """
        向所有订阅了某设备的客户端广播设备状态变更
        当设备上下线时调用此方法
        """
        message = json.dumps({
            "type": "device_status",
            "data": {"device_id": device_id, "status": status},
            "timestamp": int(time.time() * 1000),
        })
        await self._broadcast(device_id, message)

    async def broadcast_device_heartbeat(self, device_id: str, status: dict) -> None:
        """
        向所有订阅了某设备的客户端广播心跳包中的设备状态
        包含 wifi / mqtt / screen / sensor / focus_mode
        """
        message = json.dumps({
            "type": "device_heartbeat",
            "data": {"device_id": device_id, **status},
            "timestamp": int(time.time() * 1000),
        })
        await self._broadcast(device_id, message)

    async def broadcast_control_result(self, device_id: str, command: str, value: str, result: str) -> None:
        """
        向所有订阅了某设备的客户端广播控制指令执行结果
        """
        message = json.dumps({
            "type": "control_result",
            "data": {
                "device_id": device_id,
                "command": command,
                "value": value,
                "result": result,
            },
            "timestamp": int(time.time() * 1000),
        })
        await self._broadcast(device_id, message)

    async def broadcast_alert(self, device_id: str, alerts: list[dict]) -> None:
        """向订阅了某设备的客户端广播告警"""
        message = json.dumps({
            "type": "alert",
            "data": {"device_id": device_id, "alerts": alerts},
            "timestamp": int(time.time() * 1000),
        })
        await self._broadcast(device_id, message)

    async def _send_to_subscribers(self, device_id: str, message: str) -> None:
        """
        向所有订阅了某设备的客户端发送消息
        发送失败的连接会被自动移除
        """
        disconnected = []
        for ws, info in self.active_connections.items():
            if device_id in info.get("device_ids", set()):
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.append(ws)
        # 清理断开的连接
        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast_external(self, device_id: str, message: str) -> None:
        """只发送到当前 Worker，供 Redis 订阅端调用，避免重复发布。"""
        await self._send_to_subscribers(device_id, message)

    async def _broadcast(self, device_id: str, message: str) -> None:
        await self._send_to_subscribers(device_id, message)
        await redis_event_bus.publish(device_id, message)


# 全局单例实例
ws_manager = WebSocketManager()
