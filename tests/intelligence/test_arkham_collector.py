from datetime import datetime, timezone

from app.intelligence.arkham.collector import (
    ArkhamCollector,
)


class MockArkhamClient:

    def fetch_whale_events(self):

        return [
            {
                "id": "big-whale",
                "chain": "ETHEREUM",
                "event_type": "WHALE_TRANSFER",
                "direction": "OUTFLOW",
                "asset": "ETH",
                "amount_usd": 30000000,
                "from": "Binance",
                "to": "Whale Wallet",
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
            },
            {
                "id": "small-transfer",
                "chain": "ETHEREUM",
                "event_type": "WHALE_TRANSFER",
                "direction": "OUTFLOW",
                "asset": "ETH",
                "amount_usd": 500000,
                "from": "Binance",
                "to": "Wallet",
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),
            },
        ]


def test_collector_filters_whale_alerts():

    collector = ArkhamCollector(
        client=MockArkhamClient()
    )

    events = collector.collect()

    assert len(events) == 1

    assert (
        events[0].event_id
        == "big-whale"
    )

    assert (
        events[0].amount_usd
        == 30000000
    )
