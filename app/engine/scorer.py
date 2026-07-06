from app.models.event import MarketEvent


TIER_1_EXCHANGES = {
    "Binance",
    "Coinbase",
    "Coinbase Prime",
    "OKX",
    "Bybit",
}

TIER_2_EXCHANGES = {
    "Kraken",
    "Bitstamp",
    "Bitfinex",
    "Gate",
    "Gate.io",
    "KuCoin",
    "HTX",
    "Upbit",
}

IMPORTANT_ASSETS = {
    "BTC",
    "ETH",
    "BNB",
    "SOL",
    "NEAR",
    "USDT",
    "USDC",
}


def score_event(event: MarketEvent) -> dict:
    score = 0
    reasons = []
    direction = "neutral"

    if event.amount_usd >= 100_000_000:
        score += 40
        reasons.append("Very large transfer > $100M")
    elif event.amount_usd >= 50_000_000:
        score += 30
        reasons.append("Large transfer > $50M")
    elif event.amount_usd >= 10_000_000:
        score += 20
        reasons.append("Significant transfer > $10M")

    if event.asset in IMPORTANT_ASSETS:
        score += 15
        reasons.append(f"Important asset: {event.asset}")

    if event.to_entity in TIER_1_EXCHANGES:
        score += 25
        direction = "bearish"
        reasons.append(f"Funds moved to major exchange: {event.to_entity}")

    if event.from_entity in TIER_1_EXCHANGES:
        score += 20
        direction = "bullish"
        reasons.append(f"Funds moved from major exchange: {event.from_entity}")

    if event.to_entity in TIER_2_EXCHANGES:
        score += 15
        direction = "bearish"
        reasons.append(f"Funds moved to exchange: {event.to_entity}")

    if event.from_entity in TIER_2_EXCHANGES:
        score += 10
        direction = "bullish"
        reasons.append(f"Funds moved from exchange: {event.from_entity}")

    if event.from_entity == event.to_entity:
        score = 0
        direction = "ignore"
        reasons = ["Internal transfer"]

    score = min(score, 100)

    if score >= 80:
        confidence = "High"
    elif score >= 50:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        "score": score,
        "direction": direction,
        "confidence": confidence,
        "reasons": reasons,
    }
