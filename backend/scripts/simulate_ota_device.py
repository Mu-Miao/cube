import argparse
import asyncio
import hashlib
import json
import sys
import time
import uuid
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.mqtt.topics import get_control_topic, get_status_topic


def _loads(payload: bytes) -> dict:
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}


async def _download_and_verify(url: str, expected_md5: str) -> tuple[bool, str, int]:
    async with httpx.AsyncClient(timeout=60, follow_redirects=False, trust_env=False) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}", 0

    content = resp.content
    actual_md5 = hashlib.md5(content).hexdigest()
    if expected_md5 and actual_md5.lower() != expected_md5.lower():
        return False, f"MD5 mismatch: expected={expected_md5}, actual={actual_md5}", len(content)
    return True, actual_md5, len(content)


async def _publish_json(client, topic: str, payload: dict) -> None:
    await client.publish(topic, json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    print(f">>> {topic}: {json.dumps(payload, ensure_ascii=False)}")


async def simulate(device_id: str, current_version: str, timeout: int) -> int:
    try:
        import aiomqtt
    except ImportError:
        print("aiomqtt 未安装，请先安装 backend/requirements.txt")
        return 2

    status_topic = get_status_topic(device_id)
    control_topic = get_control_topic(device_id)
    client_id = f"ota-sim-{uuid.uuid4().hex[:8]}"

    async with aiomqtt.Client(
        hostname=settings.MQTT_BROKER_URL,
        port=settings.MQTT_BROKER_PORT,
        identifier=client_id,
    ) as client:
        await client.subscribe(status_topic)
        await client.subscribe(control_topic)

        await _publish_json(
            client,
            status_topic,
            {
                "device_id": device_id,
                "timestamp": int(time.time()),
                "type": "handshake",
                "chip_model": "ESP32-S3-SIM",
                "version": current_version,
            },
        )

        token = ""
        try:
            async with asyncio.timeout(timeout):
                async for message in client.messages:
                    data = _loads(message.payload)
                    msg_type = data.get("type")
                    print(f"<<< {message.topic}: {json.dumps(data, ensure_ascii=False)}")

                    if msg_type == "handshake_ack" and data.get("token"):
                        token = data["token"]
                        await _publish_json(
                            client,
                            status_topic,
                            {
                                "device_id": device_id,
                                "token": token,
                                "timestamp": int(time.time()),
                                "type": "version_check",
                                "current_version": current_version,
                            },
                        )
                        continue

                    if msg_type == "ota_update" and data.get("code") == 204:
                        print("当前已是最新版本，OTA 测试结束。")
                        return 0

                    if msg_type == "ota_update" and data.get("code") == 200:
                        url = data.get("url", "")
                        md5 = data.get("md5", "")
                        print(f"开始下载固件: {url}")
                        ok, result, size = await _download_and_verify(url, md5)
                        ack = {
                            "device_id": device_id,
                            "token": token,
                            "timestamp": int(time.time()),
                            "type": "control_ack",
                            "command": "ota_update",
                            "value": data.get("version", ""),
                            "result": "success" if ok else "failed",
                            "message": result,
                            "size": size,
                        }
                        await _publish_json(client, f"{settings.MQTT_TOPIC_PREFIX}/device/{device_id}/ack", ack)
                        if ok:
                            print(f"OTA 下载和 MD5 校验通过: size={size}, md5={result}")
                            return 0
                        print(f"OTA 测试失败: {result}, size={size}")
                        return 1
        except TimeoutError:
            print("等待 OTA 响应超时")
            return 1

    return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="模拟 ESP32 进行 OTA 版本检查和固件下载校验")
    parser.add_argument("--device-id", default="CUBE001")
    parser.add_argument("--current-version", default="v1.0.0")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(simulate(args.device_id, args.current_version, args.timeout)))


if __name__ == "__main__":
    main()
