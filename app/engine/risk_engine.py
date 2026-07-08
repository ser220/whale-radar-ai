def calculate_ai_risk(
    direction: str,
    probability: dict,
    institutional_confidence: dict,
    market_regime: dict,
    market_heat: dict,
    wallet_rank: dict,
    signal_rating: dict,
) -> dict:
    bearish = probability.get("bearish", 50)
    bullish = probability.get("bullish", 50)
    confidence = institutional_confidence.get("score", 0)
    heat = market_heat.get("score", 0)
    wallet_score = wallet_rank.get("rank", 50)
    signal_score = signal_rating.get("score", 0)
    regime = market_regime.get("regime", "Neutral")

    long_risk = 50
    short_risk = 50

    if bearish > bullish:
        long_risk += (bearish - bullish) * 0.45
        short_risk -= (bearish - bullish) * 0.25

    if bullish > bearish:
        short_risk += (bullish - bearish) * 0.45
        long_risk -= (bullish - bearish) * 0.25

    if regime in {"Distribution", "Strong Distribution"}:
        long_risk += 15
        short_risk -= 10

    if regime in {"Accumulation", "Strong Accumulation"}:
        short_risk += 15
        long_risk -= 10

    if confidence >= 80:
        if bearish > bullish:
            long_risk += 10
            short_risk -= 5
        elif bullish > bearish:
            short_risk += 10
            long_risk -= 5

    if heat >= 85:
        if bearish > bullish:
            long_risk += 8
        elif bullish > bearish:
            short_risk += 8

    if wallet_score >= 90:
        if bearish > bullish:
            long_risk += 8
        elif bullish > bearish:
            short_risk += 8

    long_risk = round(max(0, min(100, long_risk)))
    short_risk = round(max(0, min(100, short_risk)))

    continuation = max(bearish, bullish)
    reversal = 100 - continuation

    fakeout = round(max(5, min(60, 100 - signal_score)))
    bull_trap = long_risk if bearish > bullish else fakeout
    bear_trap = short_risk if bullish > bearish else fakeout

    if long_risk >= 80 and short_risk <= 40:
        recommended_bias = "SHORT"
    elif short_risk >= 80 and long_risk <= 40:
        recommended_bias = "LONG"
    else:
        recommended_bias = "WAIT"

    return {
        "long_risk": long_risk,
        "short_risk": short_risk,
        "continuation": continuation,
        "reversal": reversal,
        "fakeout": fakeout,
        "bull_trap": bull_trap,
        "bear_trap": bear_trap,
        "recommended_bias": recommended_bias,
    }
