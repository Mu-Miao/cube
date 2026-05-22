from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OperationLogItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    device_id: Optional[str] = None
    action: str
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OperationLogQuery(BaseModel):
    device_id: Optional[str] = None
    action: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class VoiceLogItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    device_id: Optional[str] = None
    command_text: Optional[str] = None
    intent: Optional[str] = None
    executed: bool = False
    response_text: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VoiceLogQuery(BaseModel):
    device_id: Optional[str] = None
    intent: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class VoiceLogCreate(BaseModel):
    device_id: str
    command_text: str
    intent: Optional[str] = None
    executed: bool = False
    response_text: Optional[str] = None
