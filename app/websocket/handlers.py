import json

from fastapi import WebSocket

from app.websocket.manager import ws_manager


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
    await ws_manager.subscribe(websocket, device_id)


async def _handle_ping(websocket: WebSocket, msg_data: dict, msg: dict) -> None:
    await websocket.send_text(json.dumps({"type": "pong"}))
