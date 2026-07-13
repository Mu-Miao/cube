# app/api/v1/ota.py
# OTA 固件更新接口
# 管理员通过 MQTT 向设备推送固件更新指令

import json
import time

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.device import Device
from app.models.user import User
from app.models.ota_log import OtaLog
from app.mqtt.client import mqtt_client
from app.mqtt.topics import get_control_topic
from app.schemas.base import ApiResponse

router = APIRouter(prefix="/ota", tags=["OTA 固件更新"])


@router.post("/push", response_model=ApiResponse)
async def push_ota_update(
    ota_data: dict,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    推送 OTA 固件更新（管理员专用）
    POST /api/v1/ota/push

    请求体：
    {
        "device_id": "CUBE001",          // 目标设备ID，"*" 表示所有在线设备
        "firmware_url": "https://...",   // 固件下载链接
        "version": "v1.1.0",             // 新版本号
        "md5": "abc123..."               // 固件文件 MD5
    }

    流程：
    1. 验证管理员权限
    2. 查找目标设备（支持单设备或批量）
    3. 通过 MQTT 发送 ota_update 消息到设备控制主题
    4. 记录推送日志
    """
    device_id = ota_data.get("device_id", "")
    firmware_url = ota_data.get("firmware_url", "")
    version = ota_data.get("version", "")
    md5 = ota_data.get("md5", "")

    # 参数校验
    if not device_id:
        return ApiResponse(code=400, message="device_id 不能为空", data=None)
    if not firmware_url:
        return ApiResponse(code=400, message="firmware_url 不能为空", data=None)
    if not version:
        return ApiResponse(code=400, message="version 不能为空", data=None)
    if not md5:
        return ApiResponse(code=400, message="md5 不能为空", data=None)

    # 构建 OTA 消息体
    ota_payload = {
        "type": "ota_update",
        "url": firmware_url,
        "version": version,
        "md5": md5,
    }
    ota_bytes = json.dumps(ota_payload, ensure_ascii=False).encode("utf-8")

    pushed_count = 0
    failed_devices = []

    if device_id == "*":
        # 批量推送：查找所有在线设备
        result = await db.execute(
            select(Device).where(Device.status == "online")
        )
        devices = result.scalars().all()

        if not devices:
            return ApiResponse(code=404, message="没有在线设备", data=None)

        for device in devices:
            try:
                await mqtt_client.publish(
                    get_control_topic(device.device_id),
                    ota_bytes,
                )
                pushed_count += 1

                # 记录日志
                log = OtaLog(
                    device_id=device.device_id,
                    target_version=version,
                    firmware_url=firmware_url,
                    firmware_md5=md5,
                    status="pushed",
                    pushed_by=admin.id,
                )
                db.add(log)
            except Exception as e:
                failed_devices.append(device.device_id)
                log = OtaLog(
                    device_id=device.device_id,
                    target_version=version,
                    firmware_url=firmware_url,
                    firmware_md5=md5,
                    status="failed",
                    pushed_by=admin.id,
                    remark=str(e),
                )
                db.add(log)
    else:
        # 单设备推送
        result = await db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        device = result.scalar_one_or_none()

        if not device:
            return ApiResponse(code=3001, message="设备不存在", data=None)

        if device.status != "online":
            return ApiResponse(code=3003, message="设备已离线", data=None)

        try:
            await mqtt_client.publish(
                get_control_topic(device_id),
                ota_bytes,
            )
            pushed_count = 1

            log = OtaLog(
                device_id=device_id,
                target_version=version,
                firmware_url=firmware_url,
                firmware_md5=md5,
                status="pushed",
                pushed_by=admin.id,
            )
            db.add(log)
        except Exception as e:
            log = OtaLog(
                device_id=device_id,
                target_version=version,
                firmware_url=firmware_url,
                firmware_md5=md5,
                status="failed",
                pushed_by=admin.id,
                remark=str(e),
            )
            db.add(log)
            return ApiResponse(code=500, message=f"推送失败: {e}", data=None)

    await db.flush()

    msg = f"已推送 {pushed_count} 台设备"
    if failed_devices:
        msg += f"，失败: {', '.join(failed_devices)}"

    return ApiResponse(message=msg, data={"pushed": pushed_count, "failed": failed_devices})


@router.get("/logs", response_model=ApiResponse)
async def get_ota_logs(
    device_id: str = Query(default=None, description="按设备ID筛选"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    查询 OTA 推送日志（管理员）
    GET /api/v1/ota/logs?device_id=CUBE001&page=1&page_size=20
    """
    query = select(OtaLog)
    if device_id:
        query = query.where(OtaLog.device_id == device_id)

    query = query.order_by(OtaLog.id.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    log_list = [
        {
            "id": log.id,
            "device_id": log.device_id,
            "target_version": log.target_version,
            "firmware_url": log.firmware_url,
            "firmware_md5": log.firmware_md5,
            "status": log.status,
            "pushed_by": log.pushed_by,
            "remark": log.remark,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]

    return ApiResponse(data=log_list)
