def calculate_institutional_score(
    asset_ai: dict,
    market_heat: dict,
    event_importance: dict,
    market_regime: dict,
    pressure: dict,
    wallet_ai: dict,
) -> dict:
    score = 0.0

    score += asset_ai.get("importance", 50) * 0.20
    score += market_heat.get("score", 0) * 0.25
    score += event_importance.get("score", 0) * 0.20

    bullish = pressure.get("bullish_pct", 0)
    bearish = pressure.get("bearish_pct", 0)
    pressure_strength = max(bullish, bearish)

    if pressure_strength >= 80:
        score += 15
    elif pressure_strength >= 60:
        score += 10
    else:
        score += 5

    reliability = wallet_ai.get("reliability", "Low")

    if reliability == "High":
        score += 10
    elif reliability == "Medium":
        score += 6
    else:
        score += 2

    risk = market_regime.get("risk", "Medium")

    if risk in {"High", "Very High"}:
        score += 10
    elif risk == "Medium":
        score += 6
    else:
        score += 2

    score = round(min(score, 100))

    if score >= 90:
        rating = "★★★★★ Institutional Grade"
    elif score >= 80:
        rating = "★★★★ Strong Institutional Signal"
    elif score >= 70:
        rating = "★★★ Active Institutional Interest"
    elif score >= 60:
        rating = "★★ Developing Signal"
    else:
        rating = "★ Low Institutional Priority"

    return {
        "score": score,
        "rating": rating,
    }
