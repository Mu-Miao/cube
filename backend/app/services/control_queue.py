import json
import time
import uuid
from collections import defaultdict
from typing import Any

from app.config import settings


class ControlQueue:
    GROUP = "cube-devices"

    def __init__(self) -> None:
        self.memory_queues: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.memory_inflight: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        self._redis = None

    async def _client(self):
        if not settings.REDIS_URL:
            return None
        if self._redis is None:
            from redis.asyncio import Redis
            self._redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    @staticmethod
    def _stream(device_id: str) -> str:
        return f"cube:control:{device_id}"

    async def enqueue(
        self,
        device_id: str,
        command: str,
        value: Any,
        params: dict[str, Any],
    ) -> str:
        command_id = uuid.uuid4().hex
        payload = {
            "command_id": command_id,
            "command": command,
            "value": value,
            "params": params,
            "attempts": 0,
        }
        redis = await self._client()
        if redis is None:
            if not settings.DEBUG:
                raise RuntimeError("生产环境控制队列需要 REDIS_URL")
            self.memory_queues[device_id].append(payload)
            return command_id

        stream = self._stream(device_id)
        try:
            await redis.xgroup_create(stream, self.GROUP, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise
        redis_id = await redis.xadd(
            stream,
            {"payload": json.dumps(payload, ensure_ascii=False)},
        )
        await redis.hset(f"{stream}:ids", command_id, redis_id)
        return command_id

    async def pull(self, device_id: str) -> dict[str, Any] | None:
        redis = await self._client()
        if redis is None:
            now = time.monotonic()
            inflight = self.memory_inflight[device_id]
            for command_id, payload in list(inflight.items()):
                elapsed = now - float(payload["_last_delivery"])
                if elapsed < settings.CONTROL_ACK_TIMEOUT_SECONDS:
                    continue
                if int(payload["attempts"]) >= settings.CONTROL_MAX_RETRIES:
                    inflight.pop(command_id, None)
                    continue
                payload["attempts"] = int(payload["attempts"]) + 1
                payload["_last_delivery"] = now
                return self._public_payload(payload)

            queue = self.memory_queues[device_id]
            if not queue:
                return None
            payload = queue.pop(0)
            payload["attempts"] = 1
            payload["_last_delivery"] = now
            self.memory_inflight[device_id][payload["command_id"]] = payload
            return self._public_payload(payload)

        stream = self._stream(device_id)
        try:
            await redis.xgroup_create(stream, self.GROUP, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise
        claimed = await redis.xautoclaim(
            stream,
            self.GROUP,
            device_id,
            min_idle_time=settings.CONTROL_ACK_TIMEOUT_SECONDS * 1000,
            start_id="0-0",
            count=1,
        )
        claimed_messages = claimed[1] if len(claimed) > 1 else []
        if claimed_messages:
            redis_id, fields = claimed_messages[0]
            payload = json.loads(fields["payload"])
            attempts = await redis.hincrby(
                f"{stream}:attempts",
                payload["command_id"],
                1,
            )
            if attempts > settings.CONTROL_MAX_RETRIES:
                await redis.xack(stream, self.GROUP, redis_id)
                await redis.xdel(stream, redis_id)
                await self._clear_redis_metadata(redis, stream, payload["command_id"])
            else:
                payload["attempts"] = attempts
                return payload

        messages = await redis.xreadgroup(
            self.GROUP,
            device_id,
            {stream: ">"},
            count=1,
            block=1,
        )
        if not messages:
            return None
        redis_id, fields = messages[0][1][0]
        payload = json.loads(fields["payload"])
        payload["attempts"] = await redis.hincrby(
            f"{stream}:attempts",
            payload["command_id"],
            1,
        )
        return payload

    async def acknowledge(self, device_id: str, command_id: str) -> bool:
        redis = await self._client()
        if redis is None:
            return self.memory_inflight[device_id].pop(command_id, None) is not None

        stream = self._stream(device_id)
        redis_id = await redis.hget(f"{stream}:ids", command_id)
        if redis_id:
            await redis.xack(stream, self.GROUP, redis_id)
            removed = await redis.xdel(stream, redis_id)
            await self._clear_redis_metadata(redis, stream, command_id)
            return bool(removed)

        pending = await redis.xpending_range(
            stream,
            self.GROUP,
            min="-",
            max="+",
            count=100,
            consumername=device_id,
        )
        for item in pending:
            redis_id = item["message_id"]
            records = await redis.xrange(stream, min=redis_id, max=redis_id)
            if records:
                payload = json.loads(records[0][1]["payload"])
                if payload.get("command_id") == command_id:
                    await redis.xack(stream, self.GROUP, redis_id)
                    await redis.xdel(stream, redis_id)
                    await self._clear_redis_metadata(redis, stream, command_id)
                    return True
        return False

    @staticmethod
    def _public_payload(payload: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in payload.items() if not key.startswith("_")}

    @staticmethod
    async def _clear_redis_metadata(redis, stream: str, command_id: str) -> None:
        await redis.hdel(f"{stream}:ids", command_id)
        await redis.hdel(f"{stream}:attempts", command_id)

    def clear_memory(self) -> None:
        self.memory_queues.clear()
        self.memory_inflight.clear()


control_queue = ControlQueue()
