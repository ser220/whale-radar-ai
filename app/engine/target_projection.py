from app.engine.adaptive_target import calculate_adaptive_move


def project_target(
    direction: str,
    current_price: float,
    probability: dict,
    institutional_confidence: dict,
    market_heat: dict,
    signal_rating: dict,
) -> dict:
    if not current_price or current_price <= 0:
        return {
            "expected_move_pct": "N/A",
            "target": "N/A",
            "eta": "N/A",
            "confidence": "Low",
            "note": "Live price unavailable.",
        }

    bearish = probability.get("bearish", 50)
    bullish = probability.get("bullish", 50)
    confidence = institutional_confidence.get("score", 0)
    heat = market_heat.get("score", 0)
    signal_score = signal_rating.get("score", 0)

    adaptive = calculate_adaptive_move(
        probability,
        institutional_confidence,
        market_heat,
        signal_rating,
        {"count": 20},
    )

    move_pct = adaptive["move_pct"]
    eta = adaptive["eta"]
    conf_label = adaptive["confidence"]

    if direction == "bearish":
        target = current_price * (1 - move_pct / 100)
        signed_move = -move_pct
        note = "Bearish projection based on institutional sell-pressure."
    elif direction == "bullish":
        target = current_price * (1 + move_pct / 100)
        signed_move = move_pct
        note = "Bullish projection based on institutional accumulation."
    else:
        target = current_price
        signed_move = 0
        note = "No directional projection."

    return {
        "expected_move_pct": f"{signed_move:+.1f}%",
        "target": f"{target:.2f}",
        "eta": eta,
        "confidence": conf_label,
        "note": note,
    }
