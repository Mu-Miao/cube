import httpx
from app.config import settings


DEVELOPMENT_STATUS = "微信推送正在开发中，当前不作为比赛 MVP 交付范围"


async def send_alert_message(content: str) -> bool:
    """正在开发中的预留接口。未配置企业微信 Webhook 时直接返回 False。"""
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
