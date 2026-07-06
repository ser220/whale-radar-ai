from app.models.event import MarketEvent
from app.storage.database import init_db, save_event

init_db()

event = MarketEvent(
    source="Arkham",
    event_type="exchange_inflow",
    asset="BNB",
    amount_usd=42_000_000,
    from_entity="Unknown Wallet",
    to_entity="Binance",
    network="BNB Chain",
    tx_hash="db_test_001",
)

save_event(event)

print("DB test completed")
