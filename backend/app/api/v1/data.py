# app/api/v1/data.py
# 数据接口
# 提供：传感器数据上传（设备侧）、最新数据查询（用户侧）

import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Integer, cast, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_owned_device
from app.db.session import get_db
from app.models.device import Device
from app.models.sensor_data import SensorData
from app.schemas.base import ApiResponse
from app.schemas.data import DeviceDataReport, DataUploadAck, SensorDataLatest, SensorDataHistoryItem
from app.services.alert_service import check_alerts
from app.services.control_status import normalize_control_status
from app.services.device_credentials import verify_device_token
from app.services.demo_data_service import (
    DEMO_REFRESH_INTERVAL_SECONDS,
    build_demo_sensor_record,
    is_live_demo_device,
    timestamp_age_seconds,
)
from app.utils.timezone import shanghai_isoformat
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/data", tags=["传感器数据"])

def _record_control_status(record: SensorData) -> dict:
    return {
        "light": bool(record.light) if record.light is not None else None,
        "light_brightness": record.light_brightness,
        "color_temperature": record.color_temperature,
        "wechat_notify": bool(record.wechat_notify) if record.wechat_notify is not None else None,
        "auto_screen_brightness": bool(record.auto_screen_brightness) if record.auto_screen_brightness is not None else None,
        "screen_brightness": record.screen_brightness,
        "focus_mode": bool(record.focus_mode) if record.focus_mode is not None else None,
    }


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
    3. 更新固件版本
    4. 通过 WebSocket 推送数据给订阅的前端客户端

    注意：此接口不需要 JWT，使用设备 Token 认证
    """
    # 验证设备 Token
    result = await db.execute(select(Device).where(Device.device_id == payload.device_id))
    device = result.scalar_one_or_none()

    if not verify_device_token(device, payload.token):
        raise HTTPException(status_code=401, detail="无效的设备凭证")

    control_status = normalize_control_status(payload.status)

    # 创建传感器数据记录
    sensor_record = SensorData(
        device_id=payload.device_id,
        temperature=payload.data.temperature,
        humidity=payload.data.humidity,
        illuminance=payload.data.illuminance,
        aqi=payload.data.aqi,
        pm25=payload.data.pm25,
        tvoc=payload.data.tvoc,
        eco2=payload.data.eco2,
        mold_risk=payload.data.mold_risk,
        gas=payload.data.gas,
        wifi_rssi=payload.data.wifi_rssi,
        focus_mode=control_status.get("focus_mode"),
        light=control_status.get("light"),
        light_brightness=control_status.get("light_brightness"),
        color_temperature=control_status.get("color_temperature"),
        wechat_notify=control_status.get("wechat_notify"),
        auto_screen_brightness=control_status.get("auto_screen_brightness"),
        screen_brightness=control_status.get("screen_brightness"),
        timestamp=datetime.fromtimestamp(payload.timestamp, tz=timezone.utc),
    )
    db.add(sensor_record)

    # 在线状态只由握手/心跳维护，避免传感器数据把失联设备顶成在线。
    if payload.data.version:
        device.firmware_version = payload.data.version

    # 先执行 INSERT，再立即推送；请求依赖会在接口正常返回时统一提交事务。
    await db.flush()

    # 通过 WebSocket 推送传感器数据给前端
    await ws_manager.broadcast_sensor_data(payload.device_id, {
        "temperature": payload.data.temperature,
        "humidity": payload.data.humidity,
        "illuminance": payload.data.illuminance,
        "aqi": payload.data.aqi,
        "pm25": payload.data.pm25,
        "tvoc": payload.data.tvoc,
        "eco2": payload.data.eco2,
        "mold_risk": payload.data.mold_risk,
        "gas": payload.data.gas,
        "wifi_rssi": payload.data.wifi_rssi,
        **control_status,
        "timestamp": shanghai_isoformat(sensor_record.timestamp),
    })

    await check_alerts(payload.device_id, {
        "gas": payload.data.gas,
        "tvoc": payload.data.tvoc,
        "eco2": payload.data.eco2,
        "mold_risk": payload.data.mold_risk,
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
    device: Device = Depends(require_owned_device),
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
    # 查询最新传感器数据（按时间戳降序，取第一条）
    data_result = await db.execute(
        select(SensorData)
        .where(SensorData.device_id == device_id)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    record = data_result.scalar_one_or_none()

    if not record and is_live_demo_device(device):
        record = build_demo_sensor_record(device_id)
        db.add(record)
        device.last_seen = record.timestamp
        await db.flush()

    if not record:
        return ApiResponse(code=0, message="暂无数据", data=None)

    if is_live_demo_device(device) and timestamp_age_seconds(record.timestamp) >= DEMO_REFRESH_INTERVAL_SECONDS:
        record = build_demo_sensor_record(device_id, record)
        db.add(record)
        device.last_seen = record.timestamp
        await db.flush()
        await ws_manager.broadcast_sensor_data(device_id, {
            "device_id": record.device_id,
            "temperature": record.temperature,
            "humidity": record.humidity,
            "illuminance": record.illuminance,
            "aqi": record.aqi,
            "pm25": record.pm25,
            "tvoc": record.tvoc,
            "eco2": record.eco2,
            "mold_risk": record.mold_risk,
            "gas": record.gas,
            "wifi_rssi": record.wifi_rssi,
            **_record_control_status(record),
            "timestamp": shanghai_isoformat(record.timestamp),
        })

    latest_data = SensorDataLatest(
        device_id=record.device_id,
        temperature=record.temperature,
        humidity=record.humidity,
        illuminance=record.illuminance,
        aqi=record.aqi,
        pm25=record.pm25,
        tvoc=record.tvoc,
        eco2=record.eco2,
        mold_risk=record.mold_risk,
        gas=record.gas,
        wifi_rssi=record.wifi_rssi,
        **_record_control_status(record),
        timestamp=record.timestamp,
    )
    return ApiResponse(data=latest_data)


@router.get("/{device_id}/history", response_model=ApiResponse[list[SensorDataHistoryItem]])
async def get_sensor_data_history(
    device_id: str,
    hours: int = Query(default=24, ge=1, le=168, description="查询最近N小时的数据"),
    limit: int = Query(default=100, ge=1, le=500, description="返回条数限制"),
    _device: Device = Depends(require_owned_device),
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
            pm25=r.pm25,
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


@router.get("/{device_id}/trend", response_model=ApiResponse[list[SensorDataHistoryItem]])
async def get_sensor_data_trend(
    device_id: str,
    hours: int = Query(default=1, description="趋势范围：1、6、24 或 168 小时"),
    _device: Device = Depends(require_owned_device),
    db: AsyncSession = Depends(get_db),
):
    """按时间桶聚合范围内的全部上传数据，供趋势图展示。"""
    bucket_seconds_by_hours = {
        1: 60,
        6: 5 * 60,
        24: 15 * 60,
        168: 60 * 60,
    }
    bucket_seconds = bucket_seconds_by_hours.get(hours)
    if bucket_seconds is None:
        raise HTTPException(status_code=422, detail="hours 仅支持 1、6、24、168")

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    if db.get_bind().dialect.name == "postgresql":
        epoch_seconds = cast(extract("epoch", SensorData.timestamp), Integer)
    else:
        epoch_seconds = cast(func.strftime("%s", SensorData.timestamp), Integer)
    bucket = cast(epoch_seconds / bucket_seconds, Integer)
    data_result = await db.execute(
        select(
            func.avg(SensorData.temperature).label("temperature"),
            func.avg(SensorData.humidity).label("humidity"),
            func.avg(SensorData.illuminance).label("illuminance"),
            func.avg(SensorData.aqi).label("aqi"),
            func.avg(SensorData.pm25).label("pm25"),
            func.avg(SensorData.tvoc).label("tvoc"),
            func.avg(SensorData.eco2).label("eco2"),
            func.avg(SensorData.mold_risk).label("mold_risk"),
            func.avg(SensorData.gas).label("gas"),
            cast(func.avg(SensorData.wifi_rssi), Integer).label("wifi_rssi"),
            func.min(SensorData.timestamp).label("timestamp"),
            func.count(SensorData.id).label("sample_count"),
        )
        .where(
            SensorData.device_id == device_id,
            SensorData.timestamp >= since,
        )
        .group_by(bucket)
        .order_by(bucket.asc())
    )

    return ApiResponse(data=[
        SensorDataHistoryItem(
            temperature=row.temperature,
            humidity=row.humidity,
            illuminance=row.illuminance,
            aqi=row.aqi,
            pm25=row.pm25,
            tvoc=row.tvoc,
            eco2=row.eco2,
            mold_risk=row.mold_risk,
            gas=row.gas,
            wifi_rssi=row.wifi_rssi,
            timestamp=row.timestamp,
            sample_count=row.sample_count,
        )
        for row in data_result.all()
    ])
