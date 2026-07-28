from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class VoiceLog(BaseModel):
    """语音日志模型 - voice_logs 表"""
    __tablename__ = "voice_logs"

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    device_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    command_text: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    intent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    executed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    response_text: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<VoiceLog(user_id={self.user_id}, intent={self.intent})>"
