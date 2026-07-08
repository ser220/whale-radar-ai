from app.models.event import MarketEvent
from app.engine.priority import get_priority
from app.engine.intelligence import explain_event
from app.engine.confidence import calculate_confidence

def format_signal(event: MarketEvent, score_data: dict) -> str:
    direction = score_data.get("direction", "neutral")
    score = score_data.get("score", 0)
    priority = get_priority(score)
    intel = explain_event(event, score_data)
    confidence = score_data.get("confidence", "Low")
    dynamic_confidence = calculate_confidence(score_data)
    reasons = score_data.get("reasons", [])

    if direction == "bearish":
        icon = "🔴"
        title = "BEARISH"
    elif direction == "bullish":
        icon = "🟢"
        title = "BULLISH"
    elif direction == "ignore":
        icon = "⚪"
        title = "IGNORED"
    else:
        icon = "🟡"
        title = "NEUTRAL"

    asset = event.asset or "UNKNOWN"
    amount = f"${event.amount_usd:,.0f}"
    reasons_text = "\n".join([f"• {r}" for r in reasons]) if reasons else "• No reasons"

    return f"""
{priority["emoji"]} <b>{priority["level"]}</b>

{icon} <b>{title} | {asset}</b>

<b>Overall AI Opinion:</b>
{intel["overall_opinion"]}

<b>Smart Money Narrative:</b>
{intel["smart_narrative"]}

<b>Institutional Score:</b>
{intel["institutional_score"]}

<b>Institutional Confidence:</b>
{intel["institutional_confidence"]}

<b>AI Probability:</b>
{intel["probability"]}

<b>Institutional Trend:</b>
{intel["institutional_trend"]}

<b>Event Importance:</b>
{intel["event_importance"]}

<b>Market Heat:</b>
{intel["market_heat"]}

<b>Asset Intelligence:</b>
{intel["asset_ai"]}

<b>Wallet Ranking:</b>
{intel["wallet_rank"]}

<b>Score:</b> {score}/100
<b>Confidence:</b> {dynamic_confidence["value"]}% ({dynamic_confidence["label"]})
<b>AI Impact:</b> {intel["impact"]}

<b>Amount:</b> {amount}
<b>From:</b> {event.from_entity or "Unknown"}
<b>To:</b> {event.to_entity or "Unknown"}
<b>Network:</b> {event.network or "Unknown"}

<b>AI View:</b>
{intel["summary"]}

<b>Action:</b>
{intel["action"]}

<b>24h Context:</b>
{intel["context"]}

<b>Exchange Context:</b>
{intel["exchange_context"]}

<b>Wallet Intelligence:</b>
{intel["wallet_ai"]}

<b>Market Regime:</b>
{intel["market_regime"]}

<b>Whale Pressure:</b>
{intel["pressure"]}

<b>Wallet Context:</b>
{intel["wallet_context"]}

<b>Reasons:</b>
{reasons_text}
""".strip()
