def calculate_institutional_confidence(
    asset_ai: dict,
    wallet_rank: dict,
    wallet_ai: dict,
    market_heat: dict,
    event_importance: dict,
    market_regime: dict,
    pressure: dict,
) -> dict:
    score = 0.0

    # Asset importance — max 20
    score += asset_ai.get("importance", 50) * 0.20

    # Wallet static rank — max 20
    score += wallet_rank.get("rank", 50) * 0.20

    # Wallet dynamic history — max 15
    reliability = wallet_ai.get("reliability", "Low")
    if reliability == "High":
        score += 15
    elif reliability == "Medium":
        score += 10
    else:
        score += 5

    # Market heat — max 15
    score += market_heat.get("score", 0) * 0.15

    # Event importance — max 10
    score += event_importance.get("score", 0) * 0.10

    # Pressure dominance — max 10
    pressure_strength = max(
        pressure.get("bullish_pct", 0),
        pressure.get("bearish_pct", 0),
    )
    if pressure_strength >= 80:
        score += 10
    elif pressure_strength >= 60:
        score += 7
    else:
        score += 4

    # Regime risk — max 10
    risk = market_regime.get("risk", "Medium")
    if risk in {"High", "Very High"}:
        score += 10
    elif risk == "Medium":
        score += 6
    else:
        score += 3

    confidence = round(min(score, 100))

    if confidence >= 90:
        label = "Very High"
    elif confidence >= 75:
        label = "High"
    elif confidence >= 60:
        label = "Medium"
    else:
        label = "Low"

    return {
        "score": confidence,
        "label": label,
    }
