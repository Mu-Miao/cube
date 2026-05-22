from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.device import Device
from app.models.user import User
from app.schemas.base import ApiResponse

router = APIRouter(prefix="/ai", tags=["AI 分析"])


async def _verify_device_ownership(device_id: str, user_id: int, db):
    result = await db.execute(
        select(Device).where(
            Device.device_id == device_id,
            Device.bound_user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


@router.get("/{device_id}/score", response_model=ApiResponse)
async def get_environment_score(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """环境综合评分（0-100）"""
    device = await _verify_device_ownership(device_id, current_user.id, db)
    if not device:
        return ApiResponse(code=3002, message="设备未绑定", data=None)

    return ApiResponse(data={
        "score": 85,
        "level": "good",
        "breakdown": {
            "temperature": 90,
            "humidity": 80,
            "air_quality": 85,
            "comfort": 88,
        },
    })


@router.get("/{device_id}/risks", response_model=ApiResponse)
async def get_risk_warnings(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """风险预警列表"""
    device = await _verify_device_ownership(device_id, current_user.id, db)
    if not device:
        return ApiResponse(code=3002, message="设备未绑定", data=None)

    return ApiResponse(data={
        "risks": [],
        "highest_level": "none",
    })


@router.get("/{device_id}/suggestions", response_model=ApiResponse)
async def get_ai_suggestions(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 建议"""
    device = await _verify_device_ownership(device_id, current_user.id, db)
    if not device:
        return ApiResponse(code=3002, message="设备未绑定", data=None)

    return ApiResponse(data={
        "suggestions": [],
    })


@router.get("/{device_id}/weekly-report", response_model=ApiResponse)
async def get_weekly_report(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """周报数据"""
    device = await _verify_device_ownership(device_id, current_user.id, db)
    if not device:
        return ApiResponse(code=3002, message="设备未绑定", data=None)

    return ApiResponse(data={
        "days": [],
    })
