from app.models.event import MarketEvent
from app.engine.context_stats import get_asset_stats
from app.engine.exchange_stats import get_exchange_stats
from app.engine.pressure import get_whale_pressure
from app.engine.wallet_profile import get_wallet_profile
from app.engine.wallet_intelligence import analyze_wallet
from app.engine.market_regime import detect_market_regime
from app.engine.opinion import build_overall_opinion


def explain_event(event: MarketEvent, score_data: dict) -> dict:
    direction = score_data.get("direction", "neutral")
    score = score_data.get("score", 0)
    cluster = score_data.get("cluster", {})

    count = cluster.get("count", 1)
    total_usd = cluster.get("total_usd", event.amount_usd)
    window = cluster.get("window_minutes", 30)

    stats_24h = get_asset_stats(event.asset, 24)

    exchange_name = event.to_entity if direction == "bearish" else event.from_entity
    exchange_stats = get_exchange_stats(exchange_name, 6) if exchange_name else {
        "count": 0,
        "total_usd": 0,
        "hours": 6,
    }

    pressure = get_whale_pressure(event.asset, 6)

    wallet_name = event.from_entity if direction == "bearish" else event.to_entity
    wallet_profile = get_wallet_profile(wallet_name)
    wallet_ai = analyze_wallet(wallet_name, direction)

    market_regime = detect_market_regime(
        direction,
        count,
        pressure,
        wallet_ai,
    )

    overall_opinion = build_overall_opinion(
        direction,
        market_regime,
        pressure,
    )

    if score >= 85:
        impact = "Very High"
    elif score >= 70:
        impact = "High"
    elif score >= 50:
        impact = "Medium"
    else:
        impact = "Low"

    context = (
        f"24h: {stats_24h['count']} {event.asset} events, "
        f"total ${stats_24h['total_usd']:,.0f}, "
        f"largest ${stats_24h['max_transfer']:,.0f}"
    )

    exchange_context = (
        f"{exchange_name or 'Unknown exchange'} 6h: "
        f"{exchange_stats['count']} whale events, "
        f"total ${exchange_stats['total_usd']:,.0f}"
    )

    pressure_text = (
        f"{event.asset} 6h: Bullish {pressure['bullish_pct']}% / "
        f"Bearish {pressure['bearish_pct']}% — {pressure['bias']}"
    )

    wallet_context = (
        f"{wallet_profile['wallet']}: seen {wallet_profile['seen']} times, "
        f"total ${wallet_profile['total_usd']:,.0f}, "
        f"avg ${wallet_profile['avg_transfer']:,.0f}"
    )

    wallet_ai_text = (
        f"Reliability: {wallet_ai['reliability']}\n"
        f"Behaviour: {wallet_ai['behavior']}\n"
        f"Advice: {wallet_ai['advice']}"
    )

    market_regime_text = (
        f"{market_regime['emoji']} {market_regime['regime']}\n"
        f"Risk: {market_regime['risk']}\n"
        f"{market_regime['message']}"
    )

    overall_opinion_text = (
        f"Bias: {overall_opinion['bias']}\n"
        f"Risk: {overall_opinion['risk']}\n"
        f"Action: {overall_opinion['action']}"
    )

    is_cluster = count >= 3 or total_usd >= 100_000_000

    if is_cluster:
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
    else:
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
        "context": context,
        "exchange_context": exchange_context,
        "pressure": pressure_text,
        "wallet_context": wallet_context,
        "wallet_ai": wallet_ai_text,
        "market_regime": market_regime_text,
        "overall_opinion": overall_opinion_text,
    }
