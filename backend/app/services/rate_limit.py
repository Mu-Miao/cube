import asyncio
import time
from collections import defaultdict, deque

from fastapi import HTTPException

from app.config import settings


class RateLimiter:
    def __init__(self) -> None:
        self._memory: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()
        self._redis = None

    async def _redis_client(self):
        if not settings.REDIS_URL:
            return None
        if self._redis is None:
            from redis.asyncio import Redis
            self._redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def check(self, key: str, limit: int, window: int = 60) -> None:
        redis = await self._redis_client()
        if redis is not None:
            redis_key = f"cube:rate:{key}"
            count = await redis.incr(redis_key)
            if count == 1:
                await redis.expire(redis_key, window)
            if count > limit:
                ttl = max(1, await redis.ttl(redis_key))
                raise HTTPException(
                    status_code=429,
                    detail="请求过于频繁，请稍后再试",
                    headers={"Retry-After": str(ttl)},
                )
            return

        if not settings.DEBUG:
            raise RuntimeError("生产环境限流需要 REDIS_URL")
        now = time.monotonic()
        async with self._lock:
            events = self._memory[key]
            while events and events[0] <= now - window:
                events.popleft()
            if len(events) >= limit:
                raise HTTPException(
                    status_code=429,
                    detail="请求过于频繁，请稍后再试",
                    headers={"Retry-After": str(window)},
                )
            events.append(now)

    def clear_memory(self) -> None:
        self._memory.clear()


auth_rate_limiter = RateLimiter()
