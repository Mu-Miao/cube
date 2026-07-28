import httpx
from app.config import settings


DEVELOPMENT_STATUS = "TTS 语音合成正在开发中，当前不作为比赛 MVP 交付范围"


async def synthesize(text: str) -> bytes | None:
    """正在开发中的预留接口。未配置第三方服务时直接返回 None。"""
    if not settings.TTS_API_URL:
        return None

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.TTS_API_URL,
                json={"text": text},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.content
    except Exception:
        pass
    return None
