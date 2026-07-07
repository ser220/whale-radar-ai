from app.models.event import MarketEvent


def explain_event(event: MarketEvent, score_data: dict) -> dict:
    direction = score_data.get("direction", "neutral")
    score = score_data.get("score", 0)
    cluster = score_data.get("cluster", {})

    count = cluster.get("count", 1)
    total_usd = cluster.get("total_usd", event.amount_usd)
    window = cluster.get("window_minutes", 30)

    impact = "Low"
    if score >= 85:
        impact = "Very High"
    elif score >= 70:
        impact = "High"
    elif score >= 50:
        impact = "Medium"

    if count >= 3 or total_usd >= 100_000_000:
        if direction == "bullish":
            summary = (
                f"Cluster outflow detected: {count} similar transfers in "
                f"{window} min, total ${total_usd:,.0f}. Possible accumulation "
                f"and reduced sell-side supply."
            )
            action = f"Watch {event.asset} for bullish continuation or pullback entry."
        elif direction == "bearish":
            summary = (
                f"Cluster inflow detected: {count} similar transfers in "
                f"{window} min, total ${total_usd:,.0f}. Elevated sell-pressure risk."
            )
            action = f"Avoid aggressive long on {event.asset}; watch support reaction."
        else:
            summary = (
                f"Cluster activity detected: {count} similar transfers in "
                f"{window} min, total ${total_usd:,.0f}."
            )
            action = "Watch only. Wait for confirmation."

        return {
            "impact": impact,
            "summary": summary,
            "action": action,
        }

    if direction == "bullish":
        summary = "Exchange outflow. Possible accumulation / reduced sell pressure."
        action = f"Watch {event.asset} for continuation or pullback entry."
    elif direction == "bearish":
        summary = "Exchange inflow. Possible sell pressure / distribution risk."
        action = f"Avoid aggressive long on {event.asset} until confirmation."
    else:
        summary = "Neutral whale transfer. No strong directional signal."
        action = "Watch only. Wait for confirmation."

    return {
        "impact": impact,
        "summary": summary,
        "action": action,
    }
