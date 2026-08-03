from app.intelligence.arkham.worker import (
    ArkhamWorker,
)

from app.intelligence.arkham.telegram_collector_adapter import (
    ArkhamTelegramCollectorAdapter,
)


class MockMessage:

    def __init__(self, text):
        self.text = text


class MockTelegramClient:

    async def iter_messages(
        self,
        entity,
        limit=10,
    ):
        yield MockMessage(
            """
[CEX Withdrawals]

From: Kraken

To: Unknown Wallet

Value: 15,000 ETH ($27,947,700.00)

Network: Ethereum

Time: 2026-08-03 14:59:23 UTC
"""
        )


class MockListener:

    async def read_recent(
        self,
        limit=10,
    ):
        from app.intelligence.arkham.telegram_parser import (
            ArkhamTelegramParser,
        )

        return [
            ArkhamTelegramParser().parse(
                """
[CEX Withdrawals]

Value: 15,000 ETH ($27,947,700.00)

Network: Ethereum
"""
            )
        ]


def test_worker_telegram_flow():

    adapter = ArkhamTelegramCollectorAdapter(
        listener=MockListener()
    )

    worker = ArkhamWorker(
        collector=adapter
    )

    events = worker.run_once()

    assert len(events) == 1

    assert (
        events[0].asset
        == "ETH"
    )

    assert (
        events[0].amount_usd
        == 27947700.00
    )
