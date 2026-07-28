# app/models/__init__.py
# SQLAlchemy ORM 模型层初始化文件
# 统一导出所有数据模型，确保导入后才能正确创建数据库表

from app.models.user import User  # noqa: F401
from app.models.device import Device  # noqa: F401
from app.models.sensor_data import SensorData  # noqa: F401
from app.models.operation_log import OperationLog  # noqa: F401
from app.models.voice_log import VoiceLog  # noqa: F401
from app.models.ota_log import OtaLog  # noqa: F401
