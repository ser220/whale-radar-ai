def calculate_probability(
    institutional_score,
    confidence,
    regime,
    pressure,
    wallet_rank,
):
    bearish = 0
    bullish = 0

    score = institutional_score["score"]

    bearish += score * 0.35

    if pressure["bearish_pct"] > pressure["bullish_pct"]:
        bearish += 20
    else:
        bullish += 20

    if regime["regime"] == "Distribution":
        bearish += 15

    if regime["regime"] == "Accumulation":
        bullish += 15

    bearish += confidence["score"] * 0.20

    if wallet_rank["rank"] >= 90:
        bearish += 10

    total = bullish + bearish

    if total == 0:
        total = 1

    bullish_pct = round(bullish / total * 100)
    bearish_pct = round(bearish / total * 100)

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
