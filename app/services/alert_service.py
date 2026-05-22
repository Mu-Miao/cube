from typing import Optional

from app.websocket.manager import ws_manager


ALERT_THRESHOLDS = {
    "gas": {
        "warning": 0.5,
        "critical": 1.0,
    },
    "tvoc": {
        "warning": 0.5,
        "critical": 1.0,
    },
    "eco2": {
        "warning": 1000,
        "critical": 2000,
    },
    "mold_risk": {
        "warning": 2,
        "critical": 3,
    },
}


async def check_alerts(device_id: str, sensor_data: dict) -> list[dict]:
    """检查传感器数据是否触发告警"""
    alerts = []

    for field, thresholds in ALERT_THRESHOLDS.items():
        value = sensor_data.get(field)
        if value is None:
            continue

        if value >= thresholds["critical"]:
            alerts.append({
                "field": field,
                "level": "critical",
                "value": value,
                "threshold": thresholds["critical"],
                "message": _get_alert_message(field, "critical", value),
            })
        elif value >= thresholds["warning"]:
            alerts.append({
                "field": field,
                "level": "warning",
                "value": value,
                "threshold": thresholds["warning"],
                "message": _get_alert_message(field, "warning", value),
            })

    if alerts:
        await ws_manager.broadcast_alert(device_id, alerts)

    return alerts


def _get_alert_message(field: str, level: str, value: float) -> str:
    messages = {
        "gas": {
            "warning": f"检测到燃气浓度偏高（{value}），请注意通风",
            "critical": f"⚠️ 燃气泄漏警告！浓度 {value}，请立即开窗通风并检查！",
        },
        "tvoc": {
            "warning": f"TVOC 浓度偏高（{value} mg/m³），建议通风",
            "critical": f"⚠️ TVOC 严重超标！浓度 {value} mg/m³，请立即通风！",
        },
        "eco2": {
            "warning": f"CO₂ 浓度偏高（{value} ppm），建议开窗换气",
            "critical": f"⚠️ CO₂ 严重超标！浓度 {value} ppm，请立即通风！",
        },
        "mold_risk": {
            "warning": f"霉菌风险等级 {value}，建议降低湿度",
            "critical": f"⚠️ 霉菌风险极高！等级 {value}，请立即除湿！",
        },
    }
    return messages.get(field, {}).get(level, f"{field} 触发 {level} 级告警")
