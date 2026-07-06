from typing import Dict


def get_priority(score: int) -> Dict[str, str]:
    """
    Converts a numerical score into a priority level.
    """

    if score >= 85:
        return {
            "level": "CRITICAL",
            "emoji": "🚨",
            "color": "red",
        }

    if score >= 70:
        return {
            "level": "HIGH",
            "emoji": "🔴",
            "color": "orange",
        }

    if score >= 50:
        return {
            "level": "MEDIUM",
            "emoji": "🟡",
            "color": "yellow",
        }

    return {
        "level": "LOW",
        "emoji": "⚪",
        "color": "grey",
    }
