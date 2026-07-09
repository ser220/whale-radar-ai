from app.engine.adaptive_weights import get_adaptive_weights


def build_adaptive_decision_shadow(probability: dict, ai_decision: dict) -> dict:
    weights = get_adaptive_weights()

    bearish = probability.get("bearish", 50)
    bullish = probability.get("bullish", 50)

    probability_weight = weights.get("Probability Engine", 1.0)
    decision_weight = weights.get("Decision Engine", 1.0)
    campaign_weight = weights.get("Campaign Detector", 1.0)

    base_confidence = ai_decision.get("overall_confidence", max(bearish, bullish))

    weighted_confidence = base_confidence
    weighted_confidence = weighted_confidence * decision_weight
    weighted_confidence = weighted_confidence * probability_weight
    weighted_confidence = weighted_confidence * campaign_weight

    weighted_confidence = max(0, min(100, round(weighted_confidence, 1)))

    difference = round(weighted_confidence - base_confidence, 1)

    if abs(difference) < 1:
        verdict = "No meaningful difference"
    elif difference > 0:
        verdict = "Adaptive model is more confident"
    else:
        verdict = "Adaptive model is less confident"

    return {
        "base_confidence": base_confidence,
        "adaptive_confidence": weighted_confidence,
        "difference": difference,
        "verdict": verdict,
        "weights": weights,
    }


def format_adaptive_decision_shadow(data: dict) -> str:
    return (
        f"Current Confidence: {data['base_confidence']}/100\n"
        f"Adaptive Confidence: {data['adaptive_confidence']}/100\n"
        f"Difference: {data['difference']:+.1f}\n"
        f"Mode: Shadow only\n"
        f"Verdict: {data['verdict']}"
    )
