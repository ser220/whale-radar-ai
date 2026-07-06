from app.models.event import MarketEvent
from app.engine.scorer import score_event

event = MarketEvent(
    source="Arkham",
    event_type="exchange_inflow",
    asset="BNB",
    amount_usd=42_000_000,
    from_entity="Unknown Wallet",
    to_entity="Binance",
    network="BNB Chain",
)

result = score_event(event)

print(result)
