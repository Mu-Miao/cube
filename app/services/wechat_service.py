import httpx
from app.config import settings


async def send_alert_message(content: str) -> bool:
    if not settings.WECHAT_WEBHOOK_URL:
        return False

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.WECHAT_WEBHOOK_URL,
                json={
                    "msgtype": "text",
                    "text": {"content": content},
                },
                timeout=10.0,
            )
            return resp.status_code == 200
    except Exception:
        return False
