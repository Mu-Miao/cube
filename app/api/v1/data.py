# app/api/v1/data.py
# 数据接口
# 提供：传感器数据上传（设备侧）、最新数据查询（用户侧）

import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.device import Device
from app.models.sensor_data import SensorData
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.data import DeviceDataReport, DataUploadAck, SensorDataLatest, SensorDataHistoryItem
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/data", tags=["传感器数据"])


@router.post("/upload", response_model=DataUploadAck)
async def upload_sensor_data(
    payload: DeviceDataReport,
    db: AsyncSession = Depends(get_db),
):
    """
    传感器数据上报接口（设备侧，Step 3）
    POST /api/v1/data/upload
    设备每 5 秒上报一次传感器数据

    流程：
    1. 验证设备 Token
    2. 将传感器数据写入数据库
    3. 更新设备在线状态
    4. 通过 WebSocket 推送数据给订阅的前端客户端

    注意：此接口不需要 JWT，使用设备 Token 认证
    """
    # 验证设备 Token
    result = await db.execute(select(Device).where(Device.device_id == payload.device_id))
    device = result.scalar_one_or_none()

    if not device or device.token != payload.token:
        raise HTTPException(status_code=401, detail="无效的设备凭证")

    # 创建传感器数据记录
    sensor_record = SensorData(
        device_id=payload.device_id,
        temperature=payload.data.temperature,
        humidity=payload.data.humidity,
        illuminance=payload.data.illuminance,
        aqi=payload.data.aqi,
        tvoc=payload.data.tvoc,
        eco2=payload.data.eco2,
        mold_risk=payload.data.mold_risk,
        gas=payload.data.gas,
        wifi_rssi=payload.data.wifi_rssi,
        focus_mode=payload.status.get("focus_mode", False) if payload.status else False,
        timestamp=datetime.fromtimestamp(payload.timestamp, tz=timezone.utc),
    )
    db.add(sensor_record)

    # 更新设备在线状态（数据上报也视为心跳）
    device.status = "online"
    device.last_seen = datetime.now(timezone.utc)

    await db.flush()

    # 通过 WebSocket 推送传感器数据给前端
    await ws_manager.broadcast_sensor_data(payload.device_id, {
        "temperature": payload.data.temperature,
        "humidity": payload.data.humidity,
        "illuminance": payload.data.illuminance,
        "aqi": payload.data.aqi,
        "tvoc": payload.data.tvoc,
        "eco2": payload.data.eco2,
        "mold_risk": payload.data.mold_risk,
        "gas": payload.data.gas,
        "wifi_rssi": payload.data.wifi_rssi,
    })

    return DataUploadAck(
        code=200,
        msg="数据接收成功",
        timestamp=int(time.time()),
        receive_status=True,
    )


@router.get("/{device_id}/latest", response_model=ApiResponse[SensorDataLatest])
async def get_latest_sensor_data(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取设备最新传感器数据（用户侧）
    GET /api/v1/data/{device_id}/latest
    需要 JWT 认证

    流程：
    1. 验证设备是否绑定到当前用户
    2. 查询该设备的最新一条传感器数据
    3. 返回数据

    错误码：3002 - 设备未绑定
    """
    # 验证设备绑定关系
    device_result = await db.execute(
        select(Device).where(
            Device.device_id == device_id,
            Device.bound_user_id == current_user.id,
        )
    )
    device = device_result.scalar_one_or_none()
    if not device:
        return ApiResponse(code=3002, message="设备未绑定", data=None)

    # 查询最新传感器数据（按时间戳降序，取第一条）
    data_result = await db.execute(
        select(SensorData)
        .where(SensorData.device_id == device_id)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    record = data_result.scalar_one_or_none()

    if not record:
        return ApiResponse(code=0, message="暂无数据", data=None)

    latest_data = SensorDataLatest(
        device_id=record.device_id,
        temperature=record.temperature,
        humidity=record.humidity,
        illuminance=record.illuminance,
        aqi=record.aqi,
        tvoc=record.tvoc,
        eco2=record.eco2,
        mold_risk=record.mold_risk,
        gas=record.gas,
        wifi_rssi=record.wifi_rssi,
        focus_mode=bool(record.focus_mode) if record.focus_mode is not None else None,
        timestamp=record.timestamp,
    )
    return ApiResponse(data=latest_data)


@router.get("/{device_id}/history", response_model=ApiResponse[list[SensorDataHistoryItem]])
async def get_sensor_data_history(
    device_id: str,
    hours: int = Query(default=24, ge=1, le=168, description="查询最近N小时的数据"),
    limit: int = Query(default=100, ge=1, le=500, description="返回条数限制"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取设备历史传感器数据（用户侧）
    GET /api/v1/data/{device_id}/history
    需要 JWT 认证

    用于 AI 分析页展示历史趋势数据

    查询参数：
      hours - 查询最近N小时的数据，默认24，最大168（7天）
      limit - 返回条数限制，默认100，最大500

    错误码：3002 - 设备未绑定
    """
    # 验证设备绑定关系
    device_result = await db.execute(
        select(Device).where(
            Device.device_id == device_id,
            Device.bound_user_id == current_user.id,
        )
    )
    device = device_result.scalar_one_or_none()
    if not device:
        return ApiResponse(code=3002, message="设备未绑定", data=None)

    # 计算时间范围
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    # 查询历史数据（按时间戳降序，取前 limit 条）
    data_result = await db.execute(
        select(SensorData)
        .where(
            SensorData.device_id == device_id,
            SensorData.timestamp >= since,
        )
        .order_by(SensorData.timestamp.desc())
        .limit(limit)
    )
    records = data_result.scalars().all()

    history_list = [
        SensorDataHistoryItem(
            temperature=r.temperature,
            humidity=r.humidity,
            illuminance=r.illuminance,
            aqi=r.aqi,
            tvoc=r.tvoc,
            eco2=r.eco2,
            mold_risk=r.mold_risk,
            gas=r.gas,
            wifi_rssi=r.wifi_rssi,
            timestamp=r.timestamp,
        )
        for r in records
    ]
    return ApiResponse(data=history_list)
