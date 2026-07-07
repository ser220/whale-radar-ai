from app.models.event import MarketEvent
from app.engine.priority import get_priority
from app.engine.intelligence import explain_event


def format_signal(event: MarketEvent, score_data: dict) -> str:
    direction = score_data.get("direction", "neutral")
    score = score_data.get("score", 0)
    priority = get_priority(score)
    intel = explain_event(event, score_data)
    confidence = score_data.get("confidence", "Low")
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

<b>Score:</b> {score}/100
<b>Confidence:</b> {confidence}
<b>AI Impact:</b> {intel["impact"]}

<b>Amount:</b> {amount}
<b>From:</b> {event.from_entity or "Unknown"}
<b>To:</b> {event.to_entity or "Unknown"}
<b>Network:</b> {event.network or "Unknown"}

<b>AI View:</b>
{intel["summary"]}

<b>Action:</b>
{intel["action"]}


<b>Reasons:</b>
{reasons_text}
""".strip()
