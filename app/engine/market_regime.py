def detect_market_regime(
    direction: str,
    cluster_count: int,
    pressure: dict,
    wallet_ai: dict,
):
    bearish = pressure.get("bearish_pct", 0)
    bullish = pressure.get("bullish_pct", 0)
    reliability = wallet_ai.get("reliability", "Low")

    if direction == "bearish" and bearish >= 90 and cluster_count >= 3 and reliability != "Low":
        return {
            "regime": "Strong Distribution",
            "emoji": "🔴",
            "risk": "Very High",
            "message": "Strong exchange inflow cluster with dominant bearish whale pressure.",
        }

    if direction == "bearish" and bearish >= 70 and reliability != "Low":
        return {
            "regime": "Distribution",
            "emoji": "🔴",
            "risk": "High",
            "message": "Large wallets continue depositing to exchanges. Sell-pressure risk dominates.",
        }

    if direction == "bullish" and bullish >= 90 and cluster_count >= 3 and reliability != "Low":
        return {
            "regime": "Strong Accumulation",
            "emoji": "🟢",
            "risk": "Low",
            "message": "Strong exchange outflow cluster with dominant bullish whale pressure.",
        }

    if direction == "bullish" and bullish >= 70 and reliability != "Low":
        return {
            "regime": "Accumulation",
            "emoji": "🟢",
            "risk": "Medium",
            "message": "Large wallets continue withdrawing from exchanges. Accumulation pressure dominates.",
        }

    return {
        "regime": "Neutral",
        "emoji": "🟡",
        "risk": "Medium",
        "message": "No clear institutional regime.",
    }
