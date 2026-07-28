from app.models.sensor_data import SensorData


def _range_score(
    value: float | None,
    ideal_min: float,
    ideal_max: float,
    hard_min: float,
    hard_max: float,
) -> int:
    if value is None:
        return 70
    if ideal_min <= value <= ideal_max:
        return 100
    if value < ideal_min:
        return max(0, round(100 * (value - hard_min) / (ideal_min - hard_min)))
    return max(0, round(100 * (hard_max - value) / (hard_max - ideal_max)))


def _lower_is_better_score(value: float | None, good: float, poor: float) -> int:
    if value is None:
        return 70
    if value <= good:
        return 100
    if value >= poor:
        return 0
    return round(100 * (poor - value) / (poor - good))


def build_score(record: SensorData | None) -> dict:
    if record is None:
        return {
            "score": 0,
            "level": "no_data",
            "breakdown": {
                "temperature": 0,
                "humidity": 0,
                "air_quality": 0,
                "comfort": 0,
            },
            "summary": "暂无传感器数据，请先连接设备并上报数据。",
        }

    temperature = _range_score(record.temperature, 22, 27, 10, 38)
    humidity = _range_score(record.humidity, 40, 65, 15, 90)
    aqi = _lower_is_better_score(record.aqi, 50, 150)
    eco2 = _lower_is_better_score(record.eco2, 800, 2000)
    tvoc = _lower_is_better_score(record.tvoc, 200, 1000)
    gas = 100 if (record.gas or 0) <= 0 else 0
    mold = _lower_is_better_score(record.mold_risk, 1, 3)
    air_quality = round(
        (aqi * 0.35) + (eco2 * 0.25) + (tvoc * 0.2) + (gas * 0.2)
    )
    comfort = round(
        (temperature * 0.45) + (humidity * 0.35) + (mold * 0.2)
    )
    score = round(
        (temperature * 0.2)
        + (humidity * 0.15)
        + (air_quality * 0.4)
        + (comfort * 0.25)
    )

    if score >= 90:
        level, summary = "excellent", "当前室内环境整体优秀，各项指标均处于舒适范围。"
    elif score >= 70:
        level, summary = "good", "当前室内环境整体良好，适合工作与休息。"
    elif score >= 40:
        level, summary = "fair", "当前室内环境一般，建议关注空气质量或湿度变化。"
    else:
        level, summary = "poor", "当前室内环境较差，请尽快通风、除湿或检查安全风险。"

    return {
        "score": score,
        "level": level,
        "breakdown": {
            "temperature": temperature,
            "humidity": humidity,
            "air_quality": air_quality,
            "comfort": comfort,
        },
        "summary": summary,
    }
