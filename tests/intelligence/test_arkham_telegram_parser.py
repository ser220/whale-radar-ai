from app.intelligence.arkham.telegram_parser import (
    ArkhamTelegramParser,
)

from app.intelligence.arkham.enums import (
    ArkhamEventType,
    ArkhamFlowDirection,
)


def test_parse_arkham_cex_withdrawal():

    message = """
[(COPY OF) CEX Withdrawals]

From: [Kraken]
To: [Unknown Wallet]

Value: 10,999,999.474300 Tether USD ($10,999,999.47)

Network: Ethereum

Time: 2026-08-03 14:53:47 UTC
"""


    event = (
        ArkhamTelegramParser()
        .parse(message)
    )


    assert (
        event.event_type
        == ArkhamEventType.CEX_WITHDRAWAL
    )

    assert (
        event.direction
        == ArkhamFlowDirection.OUTFLOW
    )

    assert (
        event.amount_usd
        == 10999999.47
    )

    assert (
        event.asset
        == "USDT"
    )


def test_invalid_message():

    import pytest

    with pytest.raises(TypeError):

        ArkhamTelegramParser().parse(
            None
        )
