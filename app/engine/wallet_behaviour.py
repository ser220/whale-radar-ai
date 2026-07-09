def analyze_wallet_behaviour(memory: dict, campaign: dict, direction: str) -> dict:
    seen = memory.get("seen", 0)
    avg_transfer = memory.get("avg_transfer", 0)
    campaign_type = campaign.get("type", "Neutral")
    campaign_confidence = campaign.get("confidence", 0)

    if direction == "bearish" and campaign_type == "Distribution":
        behaviour = "Distribution Wallet"
        message = "Wallet is repeatedly moving assets toward exchanges."
    elif direction == "bullish" and campaign_type == "Accumulation":
        behaviour = "Accumulation Wallet"
        message = "Wallet is repeatedly moving assets away from exchanges."
    elif seen >= 30 and avg_transfer >= 25_000_000:
        behaviour = "Institutional Market-Making Wallet"
        message = "Wallet shows repeated large institutional transfers."
    elif seen >= 10:
        behaviour = "Tracked Active Wallet"
        message = "Wallet has meaningful activity history."
    else:
        behaviour = "Low-History Wallet"
        message = "Not enough history to classify behaviour strongly."

    if campaign_confidence >= 90:
        confidence = "Very High"
    elif campaign_confidence >= 75:
        confidence = "High"
    elif seen >= 10:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        "behaviour": behaviour,
        "confidence": confidence,
        "message": message,
    }


def format_wallet_behaviour(data: dict) -> str:
    return (
        f"Behaviour: {data['behaviour']}\n"
        f"Confidence: {data['confidence']}\n"
        f"{data['message']}"
    )
