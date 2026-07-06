from app.models.event import MarketEvent


NOISE_KEYWORDS = [
    "FlashLender",
    "VirtualPool",
    "FlashLoan",
    "Curve.fi",
    "Balancer",
]


def is_noise_event(event: MarketEvent) -> bool:
    from_entity = event.from_entity or ""
    to_entity = event.to_entity or ""

    # Internal transfer: Binance -> Binance, OKX -> OKX, etc.
    if from_entity and to_entity and from_entity == to_entity:
        return True

    # Same exchange hot wallet transfers
    if "Binance" in from_entity and "Binance" in to_entity:
        return True
    if "Coinbase" in from_entity and "Coinbase" in to_entity:
        return True
    if "OKX" in from_entity and "OKX" in to_entity:
        return True
    if "Bybit" in from_entity and "Bybit" in to_entity:
        return True

    # DeFi noise
    combined = f"{from_entity} {to_entity}"
    for word in NOISE_KEYWORDS:
        if word.lower() in combined.lower():
            return True

    return False
