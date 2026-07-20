# app/api/v1/ota.py
# OTA 固件更新接口
# 后端通过 MQTT 下发 OTA 指令，ESP32 通过 HTTP 下载固件并自行校验、烧录、重启。

import hashlib
import json
import re
import time
from urllib.parse import urljoin

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.config import BACKEND_DIR, settings
from app.db.session import get_db
from app.models.device import Device
from app.models.ota_log import OtaLog
from app.models.user import User
from app.mqtt.client import mqtt_client
from app.mqtt.topics import get_control_topic
from app.schemas.base import ApiResponse

router = APIRouter(prefix="/ota", tags=["OTA 固件更新"])

FIRMWARE_DIR = BACKEND_DIR / "data" / "firmware"
MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")


def _normalize_url(ota_data: dict) -> str:
    return str(ota_data.get("url") or ota_data.get("firmware_url") or "").strip()


def _build_ota_payload(version: str, url: str, md5: str) -> dict:
    return {
        "code": 200,
        "type": "ota_update",
        "msg": "新版本可用",
        "timestamp": int(time.time()),
        "url": url,
        "version": version,
        "md5": md5.lower(),
    }


def _build_firmware_url(request: Request, filename: str) -> str:
    base_url = settings.FIRMWARE_PUBLIC_BASE_URL.strip() or str(request.base_url)
    if not base_url.endswith("/"):
        base_url += "/"
    return urljoin(base_url, f"firmware/{filename}")


def _validate_push_payload(ota_data: dict) -> tuple[str, str, str, str, int | None] | ApiResponse:
    device_id = str(ota_data.get("device_id") or "").strip()
    version = str(ota_data.get("version") or "").strip()
    url = _normalize_url(ota_data)
    md5 = str(ota_data.get("md5") or "").strip()
    raw_size = ota_data.get("size")

    if not device_id:
        return ApiResponse(code=400, message="device_id 不能为空", data=None)
    if not version:
        return ApiResponse(code=400, message="version 不能为空", data=None)
    if not url:
        return ApiResponse(code=400, message="url 不能为空", data=None)
    if not url.startswith(("http://", "https://")):
        return ApiResponse(code=400, message="url 必须是 HTTP/HTTPS 可访问地址", data=None)
    if not md5:
        return ApiResponse(code=400, message="md5 不能为空", data=None)
    if not MD5_RE.match(md5):
        return ApiResponse(code=400, message="md5 必须是 32 位十六进制字符串", data=None)

    size: int | None = None
    if raw_size is not None:
        try:
            size = int(raw_size)
        except (TypeError, ValueError):
            return ApiResponse(code=400, message="size 必须是正整数", data=None)
        if size <= 0:
            return ApiResponse(code=400, message="size 必须是正整数", data=None)

    return device_id, version, url, md5.lower(), size


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
        "url": "http://...",             // ESP32 可访问的固件下载链接
        "version": "v1.1.0",             // 新版本号
        "md5": "abc123..."               // 固件文件 MD5
    }

    流程：
    1. 验证管理员权限
    2. 查找目标设备（支持单设备或批量）
    3. 通过 MQTT 向 cube2026/server/{device_id}/control 发送 type=ota_update
    4. 记录推送日志
    """
    validated = _validate_push_payload(ota_data)
    if isinstance(validated, ApiResponse):
        return validated
    device_id, version, firmware_url, md5, _size = validated

    # 构建 OTA 消息体
    ota_payload = _build_ota_payload(version, firmware_url, md5)
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

    return ApiResponse(
        message=msg,
        data={
            "pushed": pushed_count,
            "failed": failed_devices,
            "payload": ota_payload,
        },
    )


@router.post("/firmware", response_model=ApiResponse)
async def upload_firmware(
    request: Request,
    version: str,
    file: UploadFile = File(...),
    _admin: User = Depends(get_current_admin),
):
    """
    上传固件并返回 OTA 推送需要的 url/md5/size。
    POST /api/v1/ota/firmware?version=1.1.0
    """
    version = version.strip()
    if not version:
        return ApiResponse(code=400, message="version 不能为空", data=None)
    if not file.filename or not file.filename.endswith(".bin"):
        return ApiResponse(code=400, message="只允许上传 .bin 固件文件", data=None)

    content = await file.read()
    if not content:
        return ApiResponse(code=400, message="固件文件不能为空", data=None)

    safe_version = re.sub(r"[^0-9A-Za-z._-]", "_", version)
    filename = f"v{safe_version}.bin" if not safe_version.startswith("v") else f"{safe_version}.bin"
    FIRMWARE_DIR.mkdir(parents=True, exist_ok=True)
    firmware_path = FIRMWARE_DIR / filename
    firmware_path.write_bytes(content)

    md5 = hashlib.md5(content).hexdigest()
    firmware_url = _build_firmware_url(request, filename)

    return ApiResponse(
        message="固件已上传",
        data={
            "version": version,
            "url": firmware_url,
            "md5": md5,
            "size": len(content),
            "filename": filename,
        },
    )


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
