from typing import Dict


def build_ai_decision(
    probability: dict,
    risk: dict,
    campaign: dict,
    event_memory: dict,
    wallet_behaviour: dict,
    scenarios: list,
) -> Dict:

    bearish = probability.get("bearish", 50)
    bullish = probability.get("bullish", 50)

    primary = scenarios[0] if scenarios else {}

    if bearish >= 90:
        conviction = "Very High"
    elif bearish >= 75:
        conviction = "High"
    elif bearish >= 60:
        conviction = "Medium"
    else:
        conviction = "Low"

    if campaign.get("confidence", 0) >= 90:
        urgency = "Immediate"
    elif campaign.get("confidence", 0) >= 70:
        urgency = "High"
    else:
        urgency = "Normal"

    if risk.get("recommended_bias") == "SHORT":
        action = "Wait for pullback and short"
    elif risk.get("recommended_bias") == "LONG":
        action = "Look for long continuation"
    else:
        action = "Wait"

    invalidation = []

    if risk.get("recommended_bias") == "SHORT":
        invalidation.extend([
            "Strong exchange outflows",
            "Bullish market regime",
            "Break above planned stop",
        ])

    else:
        invalidation.extend([
            "Large exchange inflows",
            "Distribution campaign",
            "Break below planned stop",
        ])

    return {
        "overall_confidence": primary.get("probability", max(bearish, bullish)),
        "conviction": conviction,
        "best_action": action,
        "urgency": urgency,
        "summary": primary.get("description", ""),
        "invalidates": invalidation,
    }


def format_ai_decision(decision: Dict) -> str:

    lines = [
        f"Confidence: {decision['overall_confidence']}/100",
        f"Conviction: {decision['conviction']}",
        f"Action: {decision['best_action']}",
        f"Urgency: {decision['urgency']}",
        "",
        f"Summary: {decision['summary']}",
        "",
        "Invalidation:",
    ]

    for item in decision["invalidates"]:
        lines.append(f"• {item}")

    return "\n".join(lines)
