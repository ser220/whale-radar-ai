from typing import List, Dict


def build_market_scenarios(
    direction: str,
    probability: dict,
    target_projection: dict,
    risk: dict,
) -> List[Dict]:

    bearish = probability.get("bearish", 50)
    bullish = probability.get("bullish", 50)

    target = target_projection.get("target", "N/A")
    eta = target_projection.get("eta", "Unknown")

    scenarios = []

    if direction == "bearish":

        scenarios.append({
            "title": "Primary",
            "probability": bearish,
            "emoji": "🟥",
            "description": "Distribution continues",
            "target": target,
            "eta": eta,
        })

        scenarios.append({
            "title": "Alternative",
            "probability": max(100 - bearish - 10, 5),
            "emoji": "🟨",
            "description": "Short squeeze before continuation",
            "target": "Pullback first",
            "eta": "4-12h",
        })

        scenarios.append({
            "title": "Low Probability",
            "probability": bullish,
            "emoji": "🟩",
            "description": "Bullish absorption",
            "target": "Trend invalidation",
            "eta": "Unknown",
        })

    else:

        scenarios.append({
            "title": "Primary",
            "probability": bullish,
            "emoji": "🟩",
            "description": "Accumulation continues",
            "target": target,
            "eta": eta,
        })

        scenarios.append({
            "title": "Alternative",
            "probability": max(100 - bullish - 10, 5),
            "emoji": "🟨",
            "description": "Pullback before continuation",
            "target": "Support retest",
            "eta": "4-12h",
        })

        scenarios.append({
            "title": "Low Probability",
            "probability": bearish,
            "emoji": "🟥",
            "description": "Distribution begins",
            "target": "Trend reversal",
            "eta": "Unknown",
        })

    return scenarios


def format_market_scenarios(scenarios: List[Dict]) -> str:

    lines = []

    for s in scenarios:
        lines.append(
            f"{s['emoji']} {s['title']} ({s['probability']}%)\n"
            f"{s['description']}\n"
            f"Target: {s['target']}\n"
            f"ETA: {s['eta']}"
        )

    return "\n\n".join(lines)
