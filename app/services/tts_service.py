import httpx
from app.config import settings


async def synthesize(text: str) -> bytes | None:
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
