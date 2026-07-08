def build_smart_money_narrative(
    event,
    direction: str,
    institutional_score: dict,
    institutional_confidence: dict,
    market_heat: dict,
    heat_change: dict,
    wallet_rank: dict,
    wallet_ai: dict,
    market_regime: dict,
    pressure: dict,
) -> dict:
    asset = event.asset
    from_entity = event.from_entity or "Unknown"
    to_entity = event.to_entity or "Unknown"

    score = institutional_score.get("score", 0)
    confidence = institutional_confidence.get("score", 0)
    heat = market_heat.get("score", 0)
    heat_delta = heat_change.get("change", 0)
    wallet_rank_score = wallet_rank.get("rank", 50)
    regime = market_regime.get("regime", "Neutral")
    pressure_bias = pressure.get("bias", "Neutral")

    if direction == "bearish":
        main_flow = f"{from_entity} is moving {asset} to {to_entity}."
        base_view = "This suggests potential exchange supply and sell-pressure risk."
    elif direction == "bullish":
        main_flow = f"{asset} is moving away from exchange custody."
        base_view = "This suggests possible accumulation or reduced sell-side supply."
    else:
        main_flow = f"{asset} whale activity detected."
        base_view = "Directional signal is not strong yet."

    if wallet_rank_score >= 90:
        wallet_view = "The wallet is a high-quality institutional actor."
    elif wallet_rank_score >= 75:
        wallet_view = "The wallet has strong market relevance."
    elif wallet_rank_score >= 55:
        wallet_view = "The wallet is tracked but not elite."
    else:
        wallet_view = "Wallet quality is limited or still unknown."

    if heat_delta >= 10:
        heat_view = "Institutional activity is accelerating."
    elif heat_delta <= -10:
        heat_view = "Institutional activity is fading."
    else:
        heat_view = "Institutional activity is stable."

    if score >= 85 and confidence >= 75:
        conclusion = "Signal quality is strong and should be treated as important."
    elif score >= 70:
        conclusion = "Signal is meaningful but needs confirmation."
    else:
        conclusion = "Signal is moderate and should not be used alone."

    if direction == "bearish" and regime in {"Distribution", "Strong Distribution"}:
        probability = {
            "distribution": 70,
            "absorption": 20,
            "neutral": 10,
        }
    elif direction == "bullish" and regime in {"Accumulation", "Strong Accumulation"}:
        probability = {
            "accumulation": 70,
            "distribution": 10,
            "neutral": 20,
        }
    else:
        probability = {
            "directional": 45,
            "neutral": 40,
            "opposite": 15,
        }

    text = (
        f"{main_flow}\n\n"
        f"{base_view}\n"
        f"{wallet_view}\n"
        f"{heat_view}\n\n"
        f"Regime: {regime}\n"
        f"Pressure: {pressure_bias}\n"
        f"Conclusion: {conclusion}"
    )

    return {
        "text": text,
        "probability": probability,
    }
