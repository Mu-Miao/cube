# app/schemas/base.py
# Pydantic 基础模型
# 定义统一 API 响应格式和通用数据模型

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

# 泛型类型变量，用于统一响应格式中的 data 字段
T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    统一 API 响应格式
    所有接口返回一致的 JSON 结构，方便前端统一处理

    成功响应: code=0, message="success", data=<业务数据>
    错误响应: code=<错误码>, message=<错误描述>, data=null

    错误码规范：
      0    - 成功
      400  - 请求参数错误
      401  - 认证失败
      403  - 权限不足
      500  - 服务器内部错误
      2002 - 用户名已存在
      2003 - 密码错误
      3001 - 设备不存在
      3002 - 设备未绑定
      3003 - 设备已离线
      3004 - 设备已绑定到其他用户
    """
    code: int = 0  # 状态码，0 表示成功
    message: str = "success"  # 返回信息
    data: T | None = None  # 业务数据，错误时通常为 None


class DeviceStatusPayload(BaseModel):
    """
    设备状态字段（心跳包和数据上报中的 status 子对象）
    描述设备各模块的运行状态
    """
    wifi_connected: bool  # WiFi 是否已连接
    mqtt_connected: bool  # MQTT 是否已连接（仅 MQTT 接入时为 True）
    screen_normal: bool  # 屏幕是否正常
    sensor_normal: bool  # 传感器是否正常
    focus_mode: bool  # 是否开启专注模式
