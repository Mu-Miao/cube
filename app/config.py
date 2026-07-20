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
    DEBUG: bool = True  # 调试模式，开启后自动重载
    APP_NAME: str = "智能桌面魔方 MVP"  # 应用名称

    # === OTA 固件下载配置 ===
    # ESP32 必须能访问该地址；公网演示时填 tianmuzc.site 这类可外网访问的域名。
    FIRMWARE_PUBLIC_BASE_URL: str = ""

    # === 数据库配置 ===
    # SQLite 异步连接字符串，默认在项目 data 目录下创建数据库文件
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/cube.db"

    # === JWT 认证配置 ===
    SECRET_KEY: str = "mvp-secret-key-2026-change-in-production"  # JWT 签名密钥（生产环境必须更换）
    ALGORITHM: str = "HS256"  # JWT 签名算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # Token 有效期（分钟），默认 24 小时

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
    MQTT_BROKER_URL: str = "broker.emqx.io"  # MQTT Broker 地址
    MQTT_BROKER_PORT: int = 1883  # MQTT Broker 端口
    MQTT_USERNAME: str = ""  # MQTT 用户名（可选）
    MQTT_PASSWORD: str = ""  # MQTT 密码（可选）
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

    # === WebSocket 配置 ===
    WS_PING_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100

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
