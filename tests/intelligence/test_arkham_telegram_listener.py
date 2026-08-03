import asyncio

from app.intelligence.arkham.telegram_listener import (
    ArkhamTelegramListener,
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

Value: 10,999,999.474300 Tether USD ($10,999,999.47)

Network: Ethereum

Time: 2026-08-03 14:53:47 UTC
"""
        )


def test_arkham_listener_flow():

    listener = ArkhamTelegramListener(
        client=MockTelegramClient()
    )

    events = asyncio.run(
        listener.read_recent(
            limit=1
        )
    )

    assert len(events) == 1

    assert (
        events[0].asset
        == "USDT"
    )

    assert (
        events[0].amount_usd
        == 10999999.47
    )
