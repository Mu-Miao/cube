import httpx
from app.config import settings


async def get_current_weather(city: str = "上海") -> dict | None:
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
