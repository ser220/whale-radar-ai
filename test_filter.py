from app.models.event import MarketEvent
from app.engine.filter import is_noise_event


tests = [
    MarketEvent(
        source="Arkham",
        event_type="transfer",
        asset="USDT",
        amount_usd=30_000_000,
        from_entity="Binance Hot Wallet",
        to_entity="Binance Hot Wallet",
    ),
    MarketEvent(
        source="Arkham",
        event_type="transfer",
        asset="USDT",
        amount_usd=30_000_000,
        from_entity="Unknown Wallet",
        to_entity="Binance",
    ),
    MarketEvent(
        source="Arkham",
        event_type="transfer",
        asset="crvUSD",
        amount_usd=30_000_000,
        from_entity="Yield Basis VirtualPool",
        to_entity="Curve.fi crvUSD FlashLender",
    ),
]

for event in tests:
    print(event.from_entity, "->", event.to_entity, "NOISE =", is_noise_event(event))
