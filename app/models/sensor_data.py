# app/models/sensor_data.py
# 传感器数据模型 - sensor_data 表
# 定义传感器数据表：温度、湿度、光照、空气质量等传感器读数
# 注意：device_id 不设外键，兼容未绑定设备的数据上报

from datetime import datetime

from sqlalchemy import DateTime, Double, Integer, String, func, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SensorData(BaseModel):
    """
    传感器数据模型 - sensor_data 表
    存储设备上报的所有传感器读数
    设备每 5 秒上报一次，每次写入一条记录
    device_id 不使用外键约束，允许未绑定设备上报数据
    """
    __tablename__ = "sensor_data"

    # 设备唯一标识符（与 devices 表的 device_id 对应）
    # 不设外键约束：设备可能尚未绑定用户，但仍需存储数据
    device_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # === 环境传感器数据 ===
    # 环境温度（℃）
    temperature: Mapped[float | None] = mapped_column(Double, nullable=True)
    # 环境湿度（%RH）
    humidity: Mapped[float | None] = mapped_column(Double, nullable=True)
    # 光照强度（lx 勒克斯）
    illuminance: Mapped[float | None] = mapped_column(Double, nullable=True)
    # 空气质量指数（数值越小越好）
    aqi: Mapped[float | None] = mapped_column(Double, nullable=True)
    # PM2.5 浓度（μg/m³），当前设备侧为机器学习估算值
    pm25: Mapped[float | None] = mapped_column(Double, nullable=True)
    # 有机挥发物浓度（TVOC，甲醛/异味等效）
    tvoc: Mapped[float | None] = mapped_column(Double, nullable=True)
    # CO₂ 等效浓度（ppm）
    eco2: Mapped[float | None] = mapped_column(Double, nullable=True)
    # 霉菌风险等级（0=无，1=低，2=中，3=高）
    mold_risk: Mapped[float | None] = mapped_column(Double, nullable=True)
    # 燃气浓度（0=正常，>0 表示泄漏）
    gas: Mapped[float | None] = mapped_column(Double, nullable=True)

    # === 设备状态数据 ===
    # WiFi 信号强度（dBm，典型值 -30 ~ -90）
    wifi_rssi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 专注模式状态（True=开启，False=关闭）
    focus_mode: Mapped[bool | None] = mapped_column(
        Integer, nullable=True, default=0
    )

    # 数据上报时间，由设备上报的 timestamp 字段决定
    # 区别于 created_at（服务器写入时间）
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # === 复合索引优化 ===
    # 查询某设备某时间段的数据时走此索引，大幅提升查询性能
    __table_args__ = (
        Index("ix_sensor_data_device_time", "device_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<SensorData(device_id={self.device_id}, "
            f"temp={self.temperature}, hum={self.humidity})>"
        )
