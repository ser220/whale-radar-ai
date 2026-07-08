def format_compact_signal(event, score_data, intel):
    asset = event.asset or "UNKNOWN"
    amount = f"${event.amount_usd:,.0f}"

    return f"""
{intel["alert_priority"]}

<b>{asset}</b> | {amount}

<b>AI Trade Decision:</b>
{intel["trade_decision"]}

<b>AI Probability:</b>
{intel["probability"]}

<b>Signal Rating:</b>
{intel["signal_rating"]}

<b>Smart Money Narrative:</b>
{intel["smart_narrative"]}
""".strip()
