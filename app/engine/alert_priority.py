def classify_alert_priority(signal_rating: dict) -> dict:
    priority = signal_rating.get("priority", "normal")
    score = signal_rating.get("score", 0)

    if priority == "urgent" or score >= 90:
        return {
            "level": "URGENT",
            "emoji": "🚨",
            "send": True,
            "sound": True,
            "message": "Premium institutional signal. Immediate attention recommended.",
        }

    if priority == "high" or score >= 80:
        return {
            "level": "HIGH",
            "emoji": "🔥",
            "send": True,
            "sound": False,
            "message": "Major institutional signal.",
        }

    if priority == "normal" or score >= 70:
        return {
            "level": "NORMAL",
            "emoji": "🟡",
            "send": True,
            "sound": False,
            "message": "Standard institutional signal.",
        }

    if priority == "watch" or score >= 60:
        return {
            "level": "WATCH",
            "emoji": "👀",
            "send": True,
            "sound": False,
            "message": "Developing signal. Watch only.",
        }

    return {
        "level": "LOW",
        "emoji": "⚪",
        "send": False,
        "sound": False,
        "message": "Low priority signal.",
    }
