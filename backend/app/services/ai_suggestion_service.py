from app.models.sensor_data import SensorData


def build_suggestions(record: SensorData | None) -> dict:
    if record is None:
        return {
            "suggestions": [
                {
                    "icon": "i",
                    "title": "暂无实时数据",
                    "desc": "请先连接设备并等待一次传感器上报。",
                },
            ]
        }

    suggestions: list[dict] = []
    if record.illuminance is not None and record.illuminance < 300:
        suggestions.append(
            {"icon": "light", "title": "光照偏低", "desc": "建议打开主灯或拉开窗帘。"}
        )
    if record.eco2 is not None and record.eco2 >= 1000:
        suggestions.append(
            {"icon": "wind", "title": "空气流通不足", "desc": "建议开窗通风 10-15 分钟。"}
        )
    if record.humidity is not None and record.humidity > 65:
        suggestions.append(
            {"icon": "water", "title": "湿度偏高", "desc": "建议开启除湿或加强通风。"}
        )
    if record.humidity is not None and record.humidity < 35:
        suggestions.append(
            {"icon": "water", "title": "湿度偏低", "desc": "建议适当加湿，避免长时间干燥。"}
        )
    if record.temperature is not None and record.temperature > 28:
        suggestions.append(
            {"icon": "temp", "title": "温度偏高", "desc": "建议降低空调温度或加强空气循环。"}
        )
    if record.temperature is not None and record.temperature < 18:
        suggestions.append(
            {"icon": "temp", "title": "温度偏低", "desc": "建议适当升温，保持桌面工作舒适度。"}
        )
    if not suggestions:
        suggestions.append(
            {"icon": "ok", "title": "环境状态良好", "desc": "当前环境指标比较稳定，继续保持。"}
        )
    return {"suggestions": suggestions, "source": "rule"}
