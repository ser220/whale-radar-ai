from app.engine.wallet_profile import get_wallet_profile


def analyze_wallet(wallet: str, direction: str) -> dict:
    profile = get_wallet_profile(wallet)

    seen = profile["seen"]
    avg = profile["avg_transfer"]

    reliability = "Low"
    if seen >= 20:
        reliability = "High"
    elif seen >= 8:
        reliability = "Medium"

    if direction == "bearish":
        behavior = "Repeated deposits to exchange."
    elif direction == "bullish":
        behavior = "Repeated withdrawals from exchange."
    else:
        behavior = "Mixed activity."

    if reliability == "High":
        advice = "Wallet history is statistically meaningful."
    elif reliability == "Medium":
        advice = "Historical behaviour is becoming reliable."
    else:
        advice = "Too little history for strong conclusions."

    return {
        "reliability": reliability,
        "behavior": behavior,
        "advice": advice,
        "seen": seen,
        "avg": avg,
    }
