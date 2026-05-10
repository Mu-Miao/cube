# app/mqtt/topics.py
# MQTT 主题定义
# 统一管理所有 MQTT 主题名称和订阅规则

from app.config import settings

_prefix = settings.MQTT_TOPIC_PREFIX

# 设备状态主题（设备 → 服务器）
DEVICE_STATUS_TOPIC = f"{_prefix}/device/{{device_id}}/status"

# 设备数据主题（设备 → 服务器）
DEVICE_DATA_TOPIC = f"{_prefix}/device/{{device_id}}/data"

# 设备确认主题（设备 → 服务器）
DEVICE_ACK_TOPIC = f"{_prefix}/device/{{device_id}}/ack"

# 服务器控制主题（服务器 → 设备）
SERVER_CONTROL_TOPIC = f"{_prefix}/server/{{device_id}}/control"


def get_status_topic(device_id: str) -> str:
    return DEVICE_STATUS_TOPIC.format(device_id=device_id)


def get_data_topic(device_id: str) -> str:
    return DEVICE_DATA_TOPIC.format(device_id=device_id)


def get_ack_topic(device_id: str) -> str:
    return DEVICE_ACK_TOPIC.format(device_id=device_id)


def get_control_topic(device_id: str) -> str:
    return SERVER_CONTROL_TOPIC.format(device_id=device_id)


# 通配符订阅（订阅所有设备）
SUBSCRIBE_ALL_STATUS = f"{_prefix}/device/+/status"
SUBSCRIBE_ALL_DATA = f"{_prefix}/device/+/data"
SUBSCRIBE_ALL_ACK = f"{_prefix}/device/+/ack"
