import httpx
from app.config import settings


DEVELOPMENT_STATUS = "天气服务正在开发中，当前不作为比赛 MVP 交付范围"


async def get_current_weather(city: str = "上海") -> dict | None:
    """正在开发中的预留接口。未配置第三方服务时直接返回 None。"""
    if not settings.WEATHER_API_URL or not settings.WEATHER_API_KEY:
        return None

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                settings.WEATHER_API_URL,
                params={"city": city, "key": settings.WEATHER_API_KEY},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None
