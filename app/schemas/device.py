# app/schemas/device.py
# 设备相关 Pydantic 模型
# 定义设备握手、绑定、心跳、列表查询等数据结构

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceHandshake(BaseModel):
    """
    设备握手请求体（Step 1）
    设备首次连接时发送，用于注册设备并获取临时 Token
    支持 MQTT topic: device/{device_id}/status 或 HTTP POST /api/v1/device/auth
    """
    device_id: str = Field(..., description="设备唯一标识（建议 MAC 地址）")
    timestamp: int = Field(..., description="Unix 秒时间戳")
    type: str = Field("handshake", description="消息类型，固定为 handshake")
    chip_model: str = Field(..., description="芯片型号，如 ESP32-S3")
    version: str = Field(..., description="固件版本号")


class DeviceHandshakeAck(BaseModel):
    """
    设备握手响应（handshake_ack）
    返回设备 Token，后续所有请求必须携带此 Token
    """
    code: int = 200  # 200=成功，403=失败
    type: str = "handshake_ack"  # 消息类型
    msg: str = "握手成功"  # 返回信息
    timestamp: int  # 服务器时间戳
    token: str  # 临时身份凭证
    expire_time: int = 86400  # Token 有效期（秒），默认 24 小时


class DeviceHeartbeat(BaseModel):
    """
    设备心跳包（Step 2，每 30 秒发送一次）
    用于维持设备在线状态，更新 last_seen 时间戳
    """
    device_id: str
    token: str  # 握手获取的设备 Token
    timestamp: int
    type: str = "heartbeat"
    status: dict  # 设备状态子对象（wifi_connected, screen_normal 等）


class DeviceBind(BaseModel):
    """
    用户绑定设备请求体
    POST /api/v1/device/bind
    需要用户 JWT 认证，将设备关联到当前用户
    """
    device_id: str = Field(..., description="设备唯一标识")
    device_name: str = Field("我的魔方", description="设备显示名称")


class DeviceUnbind(BaseModel):
    """
    用户解绑设备请求体
    POST /api/v1/device/unbind
    需要用户 JWT 认证，将设备从当前用户解绑
    """
    device_id: str = Field(..., description="设备唯一标识")


class DeviceItem(BaseModel):
    """
    设备列表项（GET /api/v1/device/list 返回的单条设备信息）
    """
    device_id: str  # 设备唯一标识
    device_name: str  # 设备名称
    status: str  # online / offline
    last_seen: Optional[datetime] = None  # 最后在线时间
    chip_model: Optional[str] = None  # 芯片型号
    firmware_version: Optional[str] = None  # 固件版本

    class Config:
        from_attributes = True  # 支持从 SQLAlchemy 模型转换
