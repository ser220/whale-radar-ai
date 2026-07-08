def plan_entry(
    direction: str,
    probability: dict,
    trade_decision: dict,
    market_regime: dict,
    market_heat: dict,
    signal_rating: dict,
) -> dict:
    bearish = probability.get("bearish", 50)
    bullish = probability.get("bullish", 50)
    recommendation = trade_decision.get("recommendation", "WAIT")
    setup_quality = trade_decision.get("setup_quality", 50)
    regime = market_regime.get("regime", "Neutral")
    heat = market_heat.get("score", 0)
    signal_score = signal_rating.get("score", 0)

    if recommendation == "AVOID LONGS" and bearish >= 80:
        return {
            "direction": "SHORT BIAS",
            "entry": "WAIT FOR PULLBACK / CONFIRMATION",
            "timing": "Wait for 15m confirmation before entry.",
            "reason": "Bearish probability is high and longs are not attractive.",
        }

    if direction == "bullish" and bullish >= 75 and setup_quality >= 70:
        return {
            "direction": "LONG BIAS",
            "entry": "WAIT FOR PULLBACK",
            "timing": "Wait for pullback or absorption confirmation.",
            "reason": "Bullish probability and setup quality are elevated.",
        }

    if signal_score >= 90 and heat >= 80:
        return {
            "direction": "WATCH",
            "entry": "WAIT FOR STRUCTURE CONFIRMATION",
            "timing": "Wait for market structure confirmation.",
            "reason": "Signal is strong, but entry needs price confirmation.",
        }

    return {
        "direction": "NO TRADE",
        "entry": "SKIP / WATCH ONLY",
        "timing": "No immediate entry.",
        "reason": "Setup is not clean enough for action.",
    }
