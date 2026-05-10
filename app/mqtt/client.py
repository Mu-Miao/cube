# app/mqtt/client.py
# MQTT 异步客户端
# 实现与硬件设备的 MQTT 通信连接、订阅、消息收发

import json
from contextlib import asynccontextmanager

from loguru import logger

from app.config import settings
from app.mqtt.topics import SUBSCRIBE_ALL_STATUS, SUBSCRIBE_ALL_DATA, SUBSCRIBE_ALL_ACK


class MQTTClient:
    """
    MQTT 异步客户端（可选启用）
    如果本地部署了 Mosquitto 等 MQTT Broker，则启用此客户端
    如果未部署 MQTT Broker，设备可通过 HTTP 接口接入

    功能：
      - 连接到 MQTT Broker
      - 订阅设备消息（状态、数据、确认）
      - 向设备发送消息（控制指令、ACK 响应）
    """

    def __init__(self):
        self._client = None  # aiomqtt.Client 实例
        self._running = False
        self._message_handler = None  # 消息处理回调函数

    async def connect(self, message_handler=None) -> None:
        """
        连接到 MQTT Broker 并开始监听消息

        Args:
            message_handler: 异步回调函数，接收 (topic, payload) 参数
        """
        try:
            import aiomqtt
        except ImportError:
            logger.warning("aiomqtt 未安装，MQTT 功能不可用。设备可通过 HTTP 接口接入。")
            return

        self._message_handler = message_handler
        try:
            # 构建连接参数
            connect_kwargs = {
                "hostname": settings.MQTT_BROKER_URL,
                "port": settings.MQTT_BROKER_PORT,
            }
            if settings.MQTT_USERNAME:
                connect_kwargs["username"] = settings.MQTT_USERNAME
                connect_kwargs["password"] = settings.MQTT_PASSWORD

            self._client = aiomqtt.Client(**connect_kwargs)
            await self._client.__aenter__()
            self._running = True

            # 订阅所有设备主题（通配符订阅）
            await self._client.subscribe(SUBSCRIBE_ALL_STATUS)
            await self._client.subscribe(SUBSCRIBE_ALL_DATA)
            await self._client.subscribe(SUBSCRIBE_ALL_ACK)

            logger.info(f"MQTT 已连接: {settings.MQTT_BROKER_URL}:{settings.MQTT_BROKER_PORT}")

            # 启动消息监听循环
            async for message in self._client.messages:
                if self._message_handler and self._running:
                    await self._message_handler(str(message.topic), message.payload)

        except Exception as e:
            logger.error(f"MQTT 连接失败: {e}")
            self._running = False

    async def publish(self, topic: str, payload: bytes) -> None:
        """
        向指定主题发布消息

        Args:
            topic: MQTT 主题
            payload: 消息内容（字节）
        """
        if self._client and self._running:
            try:
                await self._client.publish(topic, payload=payload)
            except Exception as e:
                logger.error(f"MQTT 发布失败 [{topic}]: {e}")

    async def disconnect(self) -> None:
        """
        断开 MQTT 连接
        """
        self._running = False
        if self._client:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception:
                pass
            logger.info("MQTT 已断开连接")


# 全局 MQTT 客户端单例
mqtt_client = MQTTClient()
