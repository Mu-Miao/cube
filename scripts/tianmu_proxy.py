"""Local reverse proxy for the tianmuzc.site SakuraFrp single-domain setup.

Run with the backend Conda environment:
    python scripts/tianmu_proxy.py

It listens on 127.0.0.1:8080 and routes backend paths to FastAPI on 8000,
while all other requests go to the Vite frontend on 4173.
"""

import asyncio
from typing import Iterable

import httpx
import uvicorn
import websockets
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response


BACKEND_BASE = "http://127.0.0.1:8000"
BACKEND_WS_BASE = "ws://127.0.0.1:8000"
FRONTEND_BASE = "http://127.0.0.1:4173"
BACKEND_PREFIXES = (
    "/api/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/firmware/",
)
HOP_BY_HOP_HEADERS = {
    "connection",
    "content-encoding",
    "content-length",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


app = FastAPI(title="tianmuzc.site local reverse proxy")


def _target_base(path: str) -> str:
    if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in BACKEND_PREFIXES):
        return BACKEND_BASE
    return FRONTEND_BASE


def _filtered_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    return {key: value for key, value in headers if key.lower() not in HOP_BY_HOP_HEADERS}


@app.websocket("/ws")
async def proxy_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    query = f"?{websocket.url.query}" if websocket.url.query else ""
    backend_url = f"{BACKEND_WS_BASE}/ws{query}"

    try:
        async with websockets.connect(backend_url) as backend_ws:

            async def client_to_backend() -> None:
                while True:
                    message = await websocket.receive_text()
                    await backend_ws.send(message)

            async def backend_to_client() -> None:
                async for message in backend_ws:
                    await websocket.send_text(message)

            done, pending = await asyncio.wait(
                {
                    asyncio.create_task(client_to_backend()),
                    asyncio.create_task(backend_to_client()),
                },
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            for task in done:
                task.result()
    except WebSocketDisconnect:
        return
    except Exception:
        await websocket.close(code=1011)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy_http(path: str, request: Request) -> Response:
    request_path = "/" + path
    target_url = httpx.URL(
        f"{_target_base(request_path)}{request_path}",
        query=request.url.query.encode("utf-8"),
    )
    body = await request.body()
    headers = _filtered_headers(request.headers.items())
    # httpx transparently decodes upstream gzip/br bodies. Ask preview/backend for
    # identity responses so forwarded headers and bodies cannot disagree.
    headers["accept-encoding"] = "identity"

    async with httpx.AsyncClient(follow_redirects=False, timeout=120.0, trust_env=False) as client:
        upstream = await client.request(
            request.method,
            target_url,
            content=body,
            headers=headers,
        )

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=_filtered_headers(upstream.headers.items()),
        media_type=upstream.headers.get("content-type"),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
