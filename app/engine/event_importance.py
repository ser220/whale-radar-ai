from app.config_assets import get_asset_importance


def calculate_event_importance(
    asset: str,
    amount_usd: float,
    confidence: int,
    pressure: dict,
    regime: dict,
    wallet_ai: dict,
):
    score = 0

    # Asset importance (0-30)
    asset_score = get_asset_importance(asset) * 0.30
    score += asset_score

    # Transfer size (0-25)
    if amount_usd >= 100_000_000:
        score += 25
    elif amount_usd >= 50_000_000:
        score += 20
    elif amount_usd >= 20_000_000:
        score += 15
    elif amount_usd >= 10_000_000:
        score += 10

    # Confidence (0-20)
    score += confidence * 0.20

    # Wallet reliability (0-10)
    if wallet_ai["reliability"] == "High":
        score += 10
    elif wallet_ai["reliability"] == "Medium":
        score += 6
    else:
        score += 2

    # Market regime (0-10)
    if regime["risk"] == "High":
        score += 10
    elif regime["risk"] == "Medium":
        score += 6

    # Whale pressure (0-5)
    if max(
        pressure["bullish_pct"],
        pressure["bearish_pct"],
    ) >= 80:
        score += 5

    importance = round(min(score, 100))

    if importance >= 90:
        label = "★★★★★ Institutional Event"

    elif importance >= 75:
        label = "★★★★ Major Whale Event"

    elif importance >= 60:
        label = "★★★ High Importance"

    elif importance >= 40:
        label = "★★ Medium Importance"

    else:
        label = "★ Minor Event"

    return {
        "score": importance,
        "label": label,
    }
