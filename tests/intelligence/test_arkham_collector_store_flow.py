from datetime import datetime, timezone

from app.intelligence.arkham.collector import (
    ArkhamCollector,
)

from app.intelligence.arkham.store import (
    ArkhamEventStore,
)


class MockArkhamClient:

    def fetch_whale_events(self):

        return [
            {
                "id": "stored-whale",
                "chain": "ETHEREUM",
                "event_type": "WHALE_TRANSFER",
                "direction": "OUTFLOW",
                "asset": "ETH",
                "amount_usd": 25000000,
                "from": "Binance",
                "to": "Whale Wallet",
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
            }
        ]


def test_collector_stores_events():

    store = ArkhamEventStore()

    collector = ArkhamCollector(
        client=MockArkhamClient(),
        store=store,
    )

    events = collector.collect()

    assert len(events) == 1

    saved = store.get(
        "stored-whale"
    )

    assert saved is not None

    assert (
        saved.amount_usd
        == 25000000
    )
