# app/models/ota_log.py
# OTA 更新日志模型 - ota_logs 表
# 记录每次 OTA 推送的目标设备、固件信息、推送结果

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class OtaLog(BaseModel):
    """
    OTA 更新日志模型
    记录每次固件推送的完整信息，用于审计和排查
    """
    __tablename__ = "ota_logs"

    # 目标设备 ID（"*" 表示批量推送所有设备）
    device_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # 推送的固件版本号
    target_version: Mapped[str] = mapped_column(String(32), nullable=False)

    # 固件下载 URL
    firmware_url: Mapped[str] = mapped_column(Text, nullable=False)

    # 固件文件 MD5 校验值
    firmware_md5: Mapped[str] = mapped_column(String(32), nullable=False)

    # 推送状态: pushed=已下发 / success=设备确认成功 / failed=下发或执行失败
    status: Mapped[str] = mapped_column(String(20), default="pushed", nullable=False)

    # 执行推送的管理员用户 ID
    pushed_by: Mapped[int] = mapped_column(Integer, nullable=False)

    # 备注信息（失败原因等）
    remark: Mapped[str] = mapped_column(Text, default="", nullable=False)

    def __repr__(self) -> str:
        return f"<OtaLog(device={self.device_id}, version={self.target_version}, status={self.status})>"
