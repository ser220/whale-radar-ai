def should_send_alert(alert_priority: dict) -> dict:
    level = alert_priority.get("level", "NORMAL")
    send = alert_priority.get("send", True)

    if not send:
        return {
            "send": False,
            "reason": "Low priority signal filtered out.",
        }

    if level == "LOW":
        return {
            "send": False,
            "reason": "Low priority signal filtered out.",
        }

    return {
        "send": True,
        "reason": f"{level} alert approved.",
    }
