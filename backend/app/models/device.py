# app/models/device.py
# 设备模型 - devices 表
# 定义设备表结构：设备唯一 ID、名称、Token、状态、绑定用户等

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Device(BaseModel):
    """
    设备数据模型 - devices 表
    记录设备的基本信息、绑定关系、在线状态
    设备必须先握手（获取 Token）才能被用户绑定
    """
    __tablename__ = "devices"

    # 设备唯一标识符，建议 MAC 地址（如 AABBCCDDEEFF）
    # 区别于自增 id，这是设备物理层面的唯一标识
    device_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # 设备显示名称，用户可自定义，默认"我的魔方"
    device_name: Mapped[str] = mapped_column(String(100), default="我的魔方", nullable=False)

    # 设备握手后获得的临时 Token，用于设备侧 API 认证
    # Token 过期后设备需重新握手
    token: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # 设备在线状态：online / offline
    # 通过心跳包维护，超过 90 秒未收到心跳自动标记为 offline
    status: Mapped[str] = mapped_column(String(20), default="offline", nullable=False)

    # 设备芯片型号，如 ESP32-S3，握手时由设备上报
    chip_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # 设备固件版本号，如 1.0.0，握手时由设备上报
    firmware_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # 绑定用户的外键，关联 users 表
    # 设备必须先被用户绑定，用户才能查看数据和控制
    bound_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # 设备最后在线时间，每次收到心跳包时更新
    # 用于判断设备是否离线（超过 90 秒未更新）
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # === 关联关系 ===
    # 关联到 User 模型，用于查询设备所属用户
    user = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Device(device_id={self.device_id}, status={self.status})>"
