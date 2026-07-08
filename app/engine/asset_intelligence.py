from app.config_assets import (
    get_asset_importance,
    get_asset_tier,
    get_asset_sector,
)


def analyze_asset(symbol: str) -> dict:

    importance = get_asset_importance(symbol)
    tier = get_asset_tier(symbol)
    sector = get_asset_sector(symbol)

    if importance >= 95:
        rating = "Institutional Core"

    elif importance >= 85:
        rating = "Institutional"

    elif importance >= 70:
        rating = "High Interest"

    else:
        rating = "Secondary"

    return {
        "importance": importance,
        "tier": tier,
        "sector": sector,
        "rating": rating,
    }
