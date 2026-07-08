def calculate_adaptive_move(
    probability: dict,
    institutional_confidence: dict,
    market_heat: dict,
    signal_rating: dict,
    similar_events: dict,
) -> dict:
    bearish = probability.get("bearish", 50)
    bullish = probability.get("bullish", 50)
    confidence = institutional_confidence.get("score", 0)
    heat = market_heat.get("score", 0)
    signal_score = signal_rating.get("score", 0)
    similar_count = similar_events.get("count", 0)

    strength = (
        max(bearish, bullish) * 0.30
        + confidence * 0.25
        + heat * 0.20
        + signal_score * 0.20
    )

    if similar_count >= 20:
        strength += 5
    elif similar_count >= 10:
        strength += 3

    strength = min(100, round(strength))

    if strength >= 92:
        move_pct = 5.5
        confidence_label = "Very High"
        eta = "12-36h"
    elif strength >= 85:
        move_pct = 4.2
        confidence_label = "High"
        eta = "8-30h"
    elif strength >= 75:
        move_pct = 3.0
        confidence_label = "Medium-High"
        eta = "6-24h"
    elif strength >= 65:
        move_pct = 2.0
        confidence_label = "Medium"
        eta = "4-18h"
    else:
        move_pct = 1.0
        confidence_label = "Low"
        eta = "Unknown"

    return {
        "strength": strength,
        "move_pct": move_pct,
        "confidence": confidence_label,
        "eta": eta,
    }
