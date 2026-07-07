def build_overall_opinion(direction: str, market_regime: dict, pressure: dict) -> dict:
    bearish = pressure.get("bearish_pct", 0)
    bullish = pressure.get("bullish_pct", 0)

    if direction == "bearish":
        bias = "Bearish"
        action = "Avoid new longs. Watch for support breakdown or absorption."
    elif direction == "bullish":
        bias = "Bullish"
        action = "Watch for continuation or pullback entry."
    else:
        bias = "Neutral"
        action = "Wait for confirmation."

    if market_regime["regime"] in {"Distribution", "Strong Distribution"}:
        bias = "Bearish"
        risk = "High"
        action = "Avoid aggressive longs. Watch for breakdown confirmation."
    elif market_regime["regime"] in {"Accumulation", "Strong Accumulation"}:
        bias = "Bullish"
        risk = "Medium"
        action = "Watch for bullish continuation or pullback entry."
    else:
        risk = "Medium"

    if bearish >= 80:
        risk = "High"
    elif bullish >= 80 and direction == "bullish":
        risk = "Medium"

    return {
        "bias": bias,
        "risk": risk,
        "action": action,
    }
