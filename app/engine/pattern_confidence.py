from app.engine.pattern_memory import get_pattern_memory


def calculate_pattern_confidence(
    asset: str,
    direction: str,
    market_regime: str,
    market_heat: str,
    wallet_behaviour: str,
    current_confidence: float,
):
    patterns = get_pattern_memory()

    key = (
        f"{asset}|{direction}|"
        f"{market_regime}|{market_heat}|"
        f"{wallet_behaviour}"
    )

    if key not in patterns:
        return {
            "current": current_confidence,
            "pattern": current_confidence,
            "difference": 0,
            "seen": 0,
            "accuracy": None,
            "mode": "No historical pattern",
        }

    p = patterns[key]

    accuracy = p["accuracy"]
    seen = p["seen"]

    adjustment = 0

    if seen >= 10:

        if accuracy >= 90:
            adjustment = 3

        elif accuracy >= 80:
            adjustment = 2

        elif accuracy >= 70:
            adjustment = 1

        elif accuracy <= 50:
            adjustment = -3

        elif accuracy <= 60:
            adjustment = -2

    new_conf = max(
        0,
        min(100, current_confidence + adjustment)
    )

    return {
        "current": current_confidence,
        "pattern": new_conf,
        "difference": round(new_conf-current_confidence, 1),
        "seen": seen,
        "accuracy": accuracy,
        "mode": "Shadow only",
    }


def format_pattern_confidence(r):

    return (
        f"Current: {r['current']}/100\n"
        f"Pattern: {r['pattern']}/100\n"
        f"Difference: {r['difference']:+}\n"
        f"Seen: {r['seen']}\n"
        f"Accuracy: {r['accuracy']}\n"
        f"Mode: {r['mode']}"
    )
