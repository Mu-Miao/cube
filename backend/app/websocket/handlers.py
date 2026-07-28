import json

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.services.device_access import find_owned_device
from app.websocket.manager import ws_manager


async def can_user_subscribe_to_device(
    db: AsyncSession,
    user_id: int,
    device_id: str,
) -> bool:
    return await find_owned_device(db, user_id, device_id) is not None


async def handle_ws_message(websocket: WebSocket, raw: str) -> None:
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        return

    msg_type = msg.get("type", "")
    msg_data = msg.get("data", msg)

    handlers = {
        "auth": _handle_auth,
        "subscribe": _handle_subscribe,
        "ping": _handle_ping,
    }

    handler = handlers.get(msg_type)
    if handler:
        await handler(websocket, msg_data, msg)


async def _handle_auth(websocket: WebSocket, msg_data: dict, msg: dict) -> None:
    token = msg_data.get("token", "") or msg.get("token", "")
    await ws_manager.authenticate(websocket, token)


async def _handle_subscribe(websocket: WebSocket, msg_data: dict, msg: dict) -> None:
    device_id = msg_data.get("device_id", "") or msg.get("device_id", "")
    user_id = ws_manager.get_authenticated_user_id(websocket)
    if user_id is None:
        await ws_manager.send_subscribe_result(websocket, 1002, "请先完成认证")
        return
    if not device_id:
        await ws_manager.send_subscribe_result(websocket, 1003, "设备 ID 不能为空")
        return

    async with async_session_factory() as db:
        if not await can_user_subscribe_to_device(db, user_id, device_id):
            await ws_manager.send_subscribe_result(websocket, 1004, "无权订阅该设备")
            return

    await ws_manager.subscribe(websocket, device_id)


async def _handle_ping(websocket: WebSocket, msg_data: dict, msg: dict) -> None:
    await websocket.send_text(json.dumps({"type": "pong"}))
