def clamp(value: int, min_value: int = 5, max_value: int = 95) -> int:
    return max(min_value, min(value, max_value))


def calculate_probability(
    institutional_score,
    confidence,
    regime,
    pressure,
    wallet_rank,
):
    bearish = 0.0
    bullish = 0.0

    score = institutional_score.get("score", 0)

    if pressure.get("bearish_pct", 0) > pressure.get("bullish_pct", 0):
        bearish += score * 0.35
        bearish += 20
    elif pressure.get("bullish_pct", 0) > pressure.get("bearish_pct", 0):
        bullish += score * 0.35
        bullish += 20
    else:
        bearish += score * 0.15
        bullish += score * 0.15

    regime_name = regime.get("regime", "Neutral")

    if regime_name in {"Distribution", "Strong Distribution"}:
        bearish += 20
    elif regime_name in {"Accumulation", "Strong Accumulation"}:
        bullish += 20

    confidence_score = confidence.get("score", 0)

    if pressure.get("bearish_pct", 0) >= 70:
        bearish += confidence_score * 0.20
    elif pressure.get("bullish_pct", 0) >= 70:
        bullish += confidence_score * 0.20

    if wallet_rank.get("rank", 50) >= 90:
        if pressure.get("bearish_pct", 0) > pressure.get("bullish_pct", 0):
            bearish += 10
        elif pressure.get("bullish_pct", 0) > pressure.get("bearish_pct", 0):
            bullish += 10

    total = bullish + bearish

    if total <= 0:
        return {
            "bullish": 50,
            "bearish": 50,
            "bias": "Neutral",
        }

    bullish_pct = round(bullish / total * 100)
    bearish_pct = round(bearish / total * 100)

    bullish_pct = clamp(bullish_pct)
    bearish_pct = clamp(bearish_pct)

    total_pct = bullish_pct + bearish_pct
    if total_pct != 100:
        if bearish_pct >= bullish_pct:
            bearish_pct = 100 - bullish_pct
        else:
            bullish_pct = 100 - bearish_pct

    if bearish_pct > bullish_pct:
        bias = "Bearish Continuation"
    elif bullish_pct > bearish_pct:
        bias = "Bullish Continuation"
    else:
        bias = "Neutral"

    return {
        "bullish": bullish_pct,
        "bearish": bearish_pct,
        "bias": bias,
    }
