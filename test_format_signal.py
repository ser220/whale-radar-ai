from app.models.event import MarketEvent
from app.engine.scorer import score_event
from app.telegram.formatter import format_signal
from app.telegram.sender import send_telegram_message


event = MarketEvent(
    source="Arkham",
    event_type="exchange_inflow",
    asset="BNB",
    amount_usd=42_000_000,
    from_entity="Unknown Wallet",
    to_entity="Binance",
    network="BNB Chain",
)

score_data = score_event(event)
message = format_signal(event, score_data)

print(message)
send_telegram_message(message)
