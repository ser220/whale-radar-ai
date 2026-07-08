from app.config_assets import get_asset_importance


def calculate_market_heat(
    asset: str,
    pressure: dict,
    exchange_stats: dict,
    wallet_ai: dict,
    regime: dict,
) -> dict:
    score = 0

    # Asset importance: 0–30
    score += get_asset_importance(asset) * 0.30

    # Whale pressure dominance: 0–20
    pressure_strength = max(
        pressure.get("bullish_pct", 0),
        pressure.get("bearish_pct", 0),
    )

    if pressure_strength >= 90:
        score += 20
    elif pressure_strength >= 75:
        score += 15
    elif pressure_strength >= 60:
        score += 10

    # Exchange activity: 0–20
    exchange_total = exchange_stats.get("total_usd", 0)

    if exchange_total >= 500_000_000:
        score += 20
    elif exchange_total >= 250_000_000:
        score += 15
    elif exchange_total >= 100_000_000:
        score += 10
    elif exchange_total >= 50_000_000:
        score += 5

    # Wallet reliability: 0–15
    reliability = wallet_ai.get("reliability", "Low")

    if reliability == "High":
        score += 15
    elif reliability == "Medium":
        score += 10
    else:
        score += 3

    # Market regime: 0–15
    risk = regime.get("risk", "Medium")

    if risk == "Very High":
        score += 15
    elif risk == "High":
        score += 12
    elif risk == "Medium":
        score += 6

    heat = round(min(score, 100))

    if heat >= 85:
        label = "🔥 Very Hot"
    elif heat >= 70:
        label = "🔥 Hot"
    elif heat >= 50:
        label = "🟡 Active"
    elif heat >= 30:
        label = "🟢 Normal"
    else:
        label = "⚪ Quiet"

    return {
        "score": heat,
        "label": label,
    }
