from app.models.event import MarketEvent
from app.engine.pipeline import process_event


for i in range(3):
    event = MarketEvent(
        source="Arkham",
        event_type="exchange_inflow",
        asset="BNB",
        amount_usd=42_000_000,
        from_entity="Unknown Wallet",
        to_entity="Binance",
        network="BNB Chain",
        tx_hash=f"test{i}",
    )

    result = process_event(event)
    print(i + 1, result)
