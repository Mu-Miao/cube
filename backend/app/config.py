# app/config.py
# Pydantic Settings 配置文件
# 集中管理所有应用配置项，从环境变量或 .env 文件读取

from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """
    应用全局配置类
    所有配置项优先从环境变量读取，其次从 .env 文件读取
    """

    # === 应用基础配置 ===
    DEBUG: bool = False
    APP_NAME: str = "智能桌面魔方 MVP"  # 应用名称
    WEB_CONCURRENCY: int = 1

    # === OTA 固件下载配置 ===
    # ESP32 必须能访问该地址；公网演示时填 tianmuzc.site 这类可外网访问的域名。
    FIRMWARE_PUBLIC_BASE_URL: str = ""

    # === 数据库配置 ===
    # SQLite 异步连接字符串，默认在项目 data 目录下创建数据库文件
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/cube.db"

    # === JWT 认证配置 ===
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"  # JWT 签名算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_COOKIE_NAME: str = "cube_refresh_token"
    REFRESH_COOKIE_SECURE: bool = False
    LOGIN_FAILURE_LIMIT: int = 10
    LOGIN_LOCKOUT_SECONDS: int = 15 * 60

    # === 设备认证配置 ===
    DEVICE_TOKEN_EXPIRE_SECONDS: int = 4 * 60 * 60
    DEVICE_PAIRING_CODE_EXPIRE_MINUTES: int = 10
    ALLOW_LEGACY_DEVICE_HANDSHAKE: bool = False

    # === CORS 跨域配置 ===
    # 允许的前端源地址列表（开发环境使用）
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "https://tianmuzc.site",
        "https://www.tianmuzc.site",
    ]

    # === MQTT 硬件对接配置 ===
    MQTT_BROKER_URL: str = ""
    MQTT_BROKER_PORT: int = 8883
    MQTT_USERNAME: str = ""  # MQTT 用户名（可选）
    MQTT_PASSWORD: str = ""  # MQTT 密码（可选）
    MQTT_TLS: bool = True
    MQTT_CA_CERT: str = ""
    MQTT_TOPIC_PREFIX: str = "cube2026"  # Topic 前缀（公共 Broker 上隔离消息）

    # === 设备心跳超时配置 ===
    # 设备心跳间隔 30 秒，超过 3 倍间隔（90 秒）未收到心跳则判定离线
    DEVICE_HEARTBEAT_TIMEOUT_SECONDS: int = 90

    # === 告警阈值配置 ===
    GAS_WARNING_THRESHOLD: float = 0.5
    GAS_CRITICAL_THRESHOLD: float = 1.0
    TVOC_WARNING_THRESHOLD: float = 0.5
    TVOC_CRITICAL_THRESHOLD: float = 1.0
    ECO2_WARNING_THRESHOLD: int = 1000
    ECO2_CRITICAL_THRESHOLD: int = 2000

    # === 数据保留策略 ===
    DATA_RETENTION_DAYS: int = 30
    FIRMWARE_MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
    JSON_MAX_REQUEST_BYTES: int = 1024 * 1024

    # === WebSocket 配置 ===
    WS_PING_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100
    WS_AUTH_TIMEOUT_SECONDS: int = 5
    WS_MAX_UNAUTHENTICATED_CONNECTIONS: int = 10

    # === Redis / 演示模式 ===
    REDIS_URL: str = ""
    DEMO_MODE: bool = False
    CONTROL_ACK_TIMEOUT_SECONDS: int = 15
    CONTROL_MAX_RETRIES: int = 3

    # === 外部服务配置（正在开发中，非当前 MVP） ===
    TTS_API_URL: str = ""
    WEATHER_API_URL: str = ""
    WEATHER_API_KEY: str = ""
    WECHAT_WEBHOOK_URL: str = ""

    # === LLM 配置 ===
    # off/api/local/auto；api 使用 OpenAI-compatible 云端接口。
    # 阿里云百炼推荐：
    #   DASHSCOPE_API_KEY=你的百炼 Key
    #   LLM_API_BASE_URL=https://llm-cvcbe2u4nm29ryl2.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
    #   LLM_API_MODEL=qwen3.6-flash
    #   LLM_API_ENABLE_THINKING=false
    LLM_MODE: str = "off"
    LLM_API_BASE_URL: str = "https://llm-cvcbe2u4nm29ryl2.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
    LLM_API_KEY: str = ""
    DASHSCOPE_API_KEY: str = ""
    LLM_API_MODEL: str = "qwen3.6-flash"
    LLM_API_ENABLE_THINKING: bool = False
    LLM_LOCAL_BASE_URL: str = "http://localhost:11434/v1"
    LLM_LOCAL_MODEL: str = "qwen2.5:3b"
    LLM_TIMEOUT: int = 120
    LLM_LOCAL_TIMEOUT: int = 120
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 512

    class Config:
        # 从 .env 文件加载配置
        env_file = BACKEND_DIR / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局单例配置实例，其他模块直接导入使用
settings = Settings()


def validate_runtime_settings() -> None:
    insecure_secrets = {
        "",
        "mvp-secret-key-2026-change-in-production",
        "change-me-in-production",
        "replace-with-at-least-32-random-characters",
    }
    if settings.SECRET_KEY in insecure_secrets or len(settings.SECRET_KEY) < 32:
        raise RuntimeError("SECRET_KEY 必须设置为至少 32 位的安全随机值")
    if settings.WEB_CONCURRENCY < 1:
        raise RuntimeError("WEB_CONCURRENCY 必须大于等于 1")
    if settings.DATABASE_URL.startswith("sqlite") and settings.WEB_CONCURRENCY != 1:
        raise RuntimeError("SQLite 仅支持 WEB_CONCURRENCY=1")
    if settings.LOGIN_FAILURE_LIMIT < 1 or settings.LOGIN_LOCKOUT_SECONDS < 1:
        raise RuntimeError("登录失败锁定阈值和时间必须大于 0")
    if settings.DEVICE_TOKEN_EXPIRE_SECONDS < 1:
        raise RuntimeError("设备 Token 有效期必须大于 0")
    if settings.JSON_MAX_REQUEST_BYTES < 1:
        raise RuntimeError("JSON 请求体上限必须大于 0")
    if not (
        1
        <= settings.WS_MAX_UNAUTHENTICATED_CONNECTIONS
        <= settings.WS_MAX_CONNECTIONS
    ):
        raise RuntimeError("WebSocket 未认证连接上限必须介于 1 和总连接上限之间")

    if not settings.DEBUG:
        if settings.DATABASE_URL.startswith("sqlite"):
            raise RuntimeError("生产环境必须使用 PostgreSQL")
        if not settings.REDIS_URL:
            raise RuntimeError("生产环境必须配置 REDIS_URL")
        public_brokers = {
            "broker.emqx.io",
            "broker.hivemq.com",
            "test.mosquitto.org",
        }
        broker_host = settings.MQTT_BROKER_URL.lower().strip().split(":", 1)[0]
        if not broker_host or broker_host in public_brokers or not settings.MQTT_TLS:
            raise RuntimeError("生产环境必须配置启用 TLS 的私有 MQTT Broker")
        if settings.MQTT_BROKER_PORT != 8883:
            raise RuntimeError("生产环境 MQTT 必须使用 TLS 端口 8883")
        if not settings.MQTT_USERNAME or not settings.MQTT_PASSWORD:
            raise RuntimeError("生产环境必须配置 MQTT 用户名和密码")
        if not settings.MQTT_CA_CERT:
            raise RuntimeError("生产环境必须配置 MQTT_CA_CERT")
        if not settings.FIRMWARE_PUBLIC_BASE_URL.startswith("https://"):
            raise RuntimeError("生产环境固件下载基址必须使用 HTTPS")
        if not settings.CORS_ORIGINS:
            raise RuntimeError("生产环境必须显式配置 CORS_ORIGINS")
        if any(
            origin == "*" or "localhost" in origin or "127.0.0.1" in origin
            for origin in settings.CORS_ORIGINS
        ):
            raise RuntimeError("生产环境 CORS_ORIGINS 禁止通配符和本地地址")
        if settings.DEMO_MODE:
            raise RuntimeError("生产环境禁止启用 DEMO_MODE")
        if not settings.REFRESH_COOKIE_SECURE:
            raise RuntimeError("生产环境必须启用 REFRESH_COOKIE_SECURE")
