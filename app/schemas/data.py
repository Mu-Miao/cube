# app/schemas/data.py
# 数据相关 Pydantic 模型
# 定义传感器数据上传、查询响应等数据结构

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class SensorDataPayload(BaseModel):
    """
    传感器数据载荷（data_report 消息中的 data 字段）
    包含所有环境传感器的读数
    """
    temperature: float = Field(..., description="温度（℃）")
    humidity: float = Field(..., description="湿度（%RH）")
    illuminance: float = Field(..., description="光照强度（lx）")
    aqi: float = Field(..., description="空气质量指数")
    pm25: Optional[float] = Field(None, description="PM2.5 浓度（μg/m³，机器学习估算值，仅供参考）")
    tvoc: float = Field(..., description="有机挥发物浓度")
    eco2: float = Field(..., description="CO₂ 等效浓度（ppm）")
    mold_risk: float = Field(..., description="霉菌风险等级（0-3）")
    gas: float = Field(..., description="燃气浓度（0=正常）")
    wifi_rssi: Optional[int] = Field(None, description="WiFi 信号强度（dBm）")
    version: Optional[str] = Field(None, description="固件版本号")


class DeviceDataReport(BaseModel):
    """
    设备数据上报请求体（Step 3，每 5 秒上报一次）
    POST /api/v1/data/upload 或通过 MQTT topic: device/{device_id}/data
    包含传感器数据和设备状态
    """
    device_id: str
    token: str  # 设备 Token，用于认证
    timestamp: int  # 数据上报时间戳
    type: str = "data_report"  # 消息类型
    data: SensorDataPayload  # 传感器数据
    status: Optional[dict] = None  # 设备状态（可选）

    @model_validator(mode="before")
    @classmethod
    def unwrap_nested_hardware_payload(cls, values):
        """
        兼容硬件 MQTT/HTTP 上报格式：
        { data: { data: {...sensor}, status: {...status} } }
        """
        if not isinstance(values, dict):
            return values

        payload = values.get("data")
        if not isinstance(payload, dict):
            return values

        nested_sensor_data = payload.get("data")
        nested_status = payload.get("status")
        if isinstance(nested_sensor_data, dict):
            normalized = values.copy()
            normalized["data"] = _normalize_pm25_key(nested_sensor_data)
            if normalized.get("status") is None and isinstance(nested_status, dict):
                normalized["status"] = nested_status
            return normalized

        normalized = values.copy()
        normalized["data"] = _normalize_pm25_key(payload)
        return normalized


class DataUploadAck(BaseModel):
    """
    数据上报响应（data_report_ack）
    """
    code: int = 200
    type: str = "data_report_ack"
    msg: str = "数据接收成功"
    timestamp: int
    receive_status: bool = True


class SensorDataHistoryItem(BaseModel):
    """
    历史传感器数据项（GET /api/v1/data/{device_id}/history 返回的单条记录）
    用于 AI 分析页展示历史趋势数据
    """
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    illuminance: Optional[float] = None
    aqi: Optional[float] = None
    pm25: Optional[float] = None
    tvoc: Optional[float] = None
    eco2: Optional[float] = None
    mold_risk: Optional[float] = None
    gas: Optional[float] = None
    wifi_rssi: Optional[int] = None
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class SensorDataLatest(BaseModel):
    """
    最新传感器数据响应（GET /api/v1/data/{device_id}/latest）
    返回设备最近一次上报的传感器读数
    """
    device_id: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    illuminance: Optional[float] = None
    aqi: Optional[float] = None
    pm25: Optional[float] = None
    tvoc: Optional[float] = None
    eco2: Optional[float] = None
    mold_risk: Optional[float] = None
    gas: Optional[float] = None
    wifi_rssi: Optional[int] = None
    focus_mode: Optional[bool] = None
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


def _normalize_pm25_key(data: dict) -> dict:
    normalized = data.copy()
    if normalized.get("pm25") is None:
        for key in ("pm2_5", "pm2.5", "PM2.5", "pm25_estimated"):
            if normalized.get(key) is not None:
                normalized["pm25"] = normalized[key]
                break
    return normalized
