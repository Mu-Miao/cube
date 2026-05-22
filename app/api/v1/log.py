from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.operation_log import OperationLog
from app.models.voice_log import VoiceLog
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.log import (
    OperationLogItem, OperationLogQuery,
    VoiceLogItem, VoiceLogQuery, VoiceLogCreate,
)

router = APIRouter(prefix="/log", tags=["日志"])


@router.get("/operation", response_model=ApiResponse)
async def list_operation_logs(
    device_id: str | None = Query(None),
    action: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询操作日志（分页）"""
    conditions = []
    if current_user.role != "admin":
        from app.models.device import Device
        device_result = await db.execute(
            select(Device.device_id).where(Device.bound_user_id == current_user.id)
        )
        user_device_ids = [d for (d,) in device_result.all()]
        conditions.append(OperationLog.device_id.in_(user_device_ids))

    if device_id:
        conditions.append(OperationLog.device_id == device_id)
    if action:
        conditions.append(OperationLog.action == action)

    count_stmt = select(func.count(OperationLog.id))
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = select(OperationLog).order_by(OperationLog.created_at.desc())
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    items = [OperationLogItem.model_validate(log) for log in logs]
    return ApiResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/voice", response_model=ApiResponse)
async def list_voice_logs(
    device_id: str | None = Query(None),
    intent: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询语音日志（分页）"""
    conditions = []
    if current_user.role != "admin":
        from app.models.device import Device
        device_result = await db.execute(
            select(Device.device_id).where(Device.bound_user_id == current_user.id)
        )
        user_device_ids = [d for (d,) in device_result.all()]
        conditions.append(VoiceLog.device_id.in_(user_device_ids))

    if device_id:
        conditions.append(VoiceLog.device_id == device_id)
    if intent:
        conditions.append(VoiceLog.intent == intent)

    count_stmt = select(func.count(VoiceLog.id))
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = select(VoiceLog).order_by(VoiceLog.created_at.desc())
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    logs = result.scalars().all()

    items = [VoiceLogItem.model_validate(log) for log in logs]
    return ApiResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/voice", response_model=ApiResponse)
async def create_voice_log(
    log_data: VoiceLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建语音日志"""
    log = VoiceLog(
        user_id=current_user.id,
        device_id=log_data.device_id,
        command_text=log_data.command_text,
        intent=log_data.intent,
        executed=log_data.executed,
        response_text=log_data.response_text,
    )
    db.add(log)
    await db.flush()
    return ApiResponse(message="语音日志已记录")
