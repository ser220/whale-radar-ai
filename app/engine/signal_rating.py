def calculate_signal_rating(
    institutional_score: dict,
    institutional_confidence: dict,
    probability: dict,
    trade_decision: dict,
    similar_events: dict,
) -> dict:
    score = 0.0

    score += institutional_score.get("score", 0) * 0.30
    score += institutional_confidence.get("score", 0) * 0.25

    bearish = probability.get("bearish", 50)
    bullish = probability.get("bullish", 50)
    probability_strength = max(bearish, bullish)
    score += probability_strength * 0.20

    score += trade_decision.get("setup_quality", 0) * 0.15

    if similar_events.get("count", 0) >= 10:
        score += 10
    elif similar_events.get("count", 0) >= 5:
        score += 5

    score = round(min(score, 100))

    if score >= 90:
        label = "★★★★★ Premium Institutional Signal"
        priority = "urgent"
    elif score >= 80:
        label = "★★★★ Major Institutional Signal"
        priority = "high"
    elif score >= 70:
        label = "★★★ Standard Institutional Signal"
        priority = "normal"
    elif score >= 60:
        label = "★★ Developing Signal"
        priority = "watch"
    else:
        label = "★ Low Priority"
        priority = "low"

    return {
        "score": score,
        "label": label,
        "priority": priority,
    }
