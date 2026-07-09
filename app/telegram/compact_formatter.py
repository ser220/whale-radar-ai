def format_compact_signal(event, score_data, intel):
    asset = event.asset or "UNKNOWN"
    amount = f"${event.amount_usd:,.0f}"

    return f"""
{intel["alert_priority"]}

<b>{asset}</b> | {amount}

<b>AI Trade Decision:</b>
{intel["trade_decision"]}

<b>AI Entry Plan:</b>
{intel["entry_plan"]}

<b>AI Price Plan:</b>
{intel["price_plan"]}

<b>AI Target Projection:</b>
{intel["target_projection"]}

<b>AI Risk Assessment:</b>
{intel["ai_risk"]}

<b>AI Market Scenarios:</b>
{intel["market_scenarios"]}

<b>AI Final Decision:</b>
{intel["ai_decision"]}

<b>AI Probability:</b>
{intel["probability"]}

<b>Signal Rating:</b>
{intel["signal_rating"]}

<b>Source Consensus:</b>
{intel["source_consensus"]}

<b>Institutional Campaign:</b>
{intel["campaign"]}

<b>Wallet Memory:</b>
{intel["wallet_memory"]}

<b>Wallet Behaviour:</b>
{intel["wallet_behaviour"]}

<b>Event Memory:</b>
{intel["event_memory"]}

<b>Smart Money Narrative:</b>
{intel["smart_narrative"]}
""".strip()
