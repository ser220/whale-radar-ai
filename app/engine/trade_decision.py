def build_trade_decision(
    direction: str,
    probability: dict,
    institutional_confidence: dict,
    market_regime: dict,
    market_heat: dict,
    wallet_rank: dict,
) -> dict:
    bearish = probability.get("bearish", 50)
    bullish = probability.get("bullish", 50)
    confidence = institutional_confidence.get("score", 0)
    regime = market_regime.get("regime", "Neutral")
    heat = market_heat.get("score", 0)
    wallet_score = wallet_rank.get("rank", 50)

    recommendation = "WAIT"
    risk_reward = "Neutral"
    setup_quality = 50
    reason = []

    if direction == "bearish" and bearish >= 80 and confidence >= 70:
        recommendation = "AVOID LONGS"
        risk_reward = "Poor for longs"
        setup_quality = min(95, round((bearish + confidence + heat) / 3))
        reason.append("High bearish probability")
        reason.append("Exchange inflow detected")

        if regime in {"Distribution", "Strong Distribution"}:
            reason.append("Distribution regime")

        if wallet_score >= 85:
            reason.append("High-quality wallet involved")

    elif direction == "bullish" and bullish >= 75 and confidence >= 70:
        recommendation = "WATCH LONG"
        risk_reward = "Potentially attractive"
        setup_quality = min(95, round((bullish + confidence + heat) / 3))
        reason.append("Bullish probability is elevated")
        reason.append("Exchange outflow / accumulation signal")

        if regime in {"Accumulation", "Strong Accumulation"}:
            reason.append("Accumulation regime")

        if wallet_score >= 85:
            reason.append("High-quality wallet involved")

    elif confidence < 60:
        recommendation = "LOW CONFIDENCE"
        risk_reward = "Unclear"
        setup_quality = confidence
        reason.append("Signal confidence is low")

    else:
        recommendation = "WAIT"
        risk_reward = "Not attractive yet"
        setup_quality = round((confidence + heat) / 2)
        reason.append("Signal needs confirmation")

    return {
        "recommendation": recommendation,
        "setup_quality": setup_quality,
        "risk_reward": risk_reward,
        "reason": reason,
    }
