from app.models.sensor_data import SensorData


def build_risks(record: SensorData | None) -> dict:
    if record is None:
        return {"risks": [], "highest_level": "none"}

    risks: list[dict] = []

    def add(field: str, level: str, title: str, message: str) -> None:
        risks.append(
            {
                "field": field,
                "level": level,
                "title": title,
                "message": message,
            }
        )

    if (record.gas or 0) > 0:
        add("gas", "critical", "燃气安全异常", "检测到燃气风险，请立即开窗通风并检查气源。")
    if (record.mold_risk or 0) >= 3:
        add(
            "mold_risk",
            "critical",
            "霉菌风险极高",
            "湿度或环境条件已达到高风险，请尽快除湿并检查墙角/织物。",
        )
    elif (record.mold_risk or 0) >= 2:
        add("mold_risk", "warning", "霉菌风险偏高", "建议降低湿度，保持空气流通。")
    if (record.eco2 or 0) >= 1500:
        add("eco2", "critical", "CO2 浓度过高", "建议立即开窗通风，避免长时间停留。")
    elif (record.eco2 or 0) >= 1000:
        add("eco2", "warning", "CO2 浓度偏高", "建议通风 10-15 分钟。")
    if (record.tvoc or 0) >= 1000:
        add("tvoc", "critical", "TVOC 严重超标", "建议立即通风，并排查异味或装修污染来源。")
    elif (record.tvoc or 0) >= 500:
        add("tvoc", "warning", "TVOC 偏高", "建议打开窗户或空气净化设备。")

    level_rank = {"none": 0, "warning": 1, "critical": 2}
    highest = "none"
    for risk in risks:
        if level_rank[risk["level"]] > level_rank[highest]:
            highest = risk["level"]
    return {"risks": risks, "highest_level": highest}
