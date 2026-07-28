import asyncio
import json
import uuid
from collections.abc import Awaitable, Callable

from loguru import logger

from app.config import settings


class RedisEventBus:
    CHANNEL = "cube:websocket:broadcast"

    def __init__(self) -> None:
        self.instance_id = uuid.uuid4().hex
        self._redis = None
        self._running = False
        self.connected = False
        self.failure_count = 0
        self.last_error: str | None = None

    async def _client(self):
        if not settings.REDIS_URL:
            return None
        if self._redis is None:
            from redis.asyncio import Redis
            self._redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def publish(self, device_id: str, message: str) -> None:
        try:
            redis = await self._client()
            if redis is None:
                return
            await redis.publish(self.CHANNEL, json.dumps({
                "origin": self.instance_id,
                "device_id": device_id,
                "message": message,
            }))
        except Exception:
            logger.exception("Redis WebSocket 广播发布失败")

    async def ping(self) -> bool | None:
        redis = await self._client()
        if redis is None:
            return None
        return bool(await redis.ping())

    async def listen(
        self,
        handler: Callable[[str, str], Awaitable[None]],
    ) -> None:
        if not settings.REDIS_URL:
            return
        self._running = True
        retry_delay = 1.0
        while self._running:
            pubsub = None
            try:
                redis = await self._client()
                pubsub = redis.pubsub()
                await pubsub.subscribe(self.CHANNEL)
                self.connected = True
                self.last_error = None
                retry_delay = 1.0
                while self._running:
                    event = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1,
                    )
                    if not event:
                        await asyncio.sleep(0)
                        continue
                    try:
                        payload = json.loads(event["data"])
                        if payload.get("origin") == self.instance_id:
                            continue
                        await handler(payload["device_id"], payload["message"])
                    except (KeyError, TypeError, json.JSONDecodeError):
                        logger.warning("忽略无效 Redis WebSocket 广播事件")
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.connected = False
                self.failure_count += 1
                self.last_error = str(exc)
                logger.warning(
                    "Redis WebSocket 广播监听中断，{} 秒后重试: {}",
                    retry_delay,
                    exc,
                )
                if self._redis is not None:
                    await self._redis.aclose()
                    self._redis = None
                if self._running:
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 30.0)
            finally:
                self.connected = False
                if pubsub is not None:
                    try:
                        await pubsub.unsubscribe(self.CHANNEL)
                        await pubsub.aclose()
                    except Exception:
                        logger.debug("关闭 Redis Pub/Sub 连接时出现异常")

    async def close(self) -> None:
        self._running = False
        self.connected = False
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None


redis_event_bus = RedisEventBus()
