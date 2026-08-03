from datetime import datetime, timezone

import pytest

from app.intelligence.arkham.parser import (
    ArkhamEventParser,
)

from app.intelligence.arkham.models import (
    ArkhamWhaleEvent,
)


def build_payload():

    return {
        "id": "tx-001",
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
    }


def test_arkham_payload_parses_to_event():

    event = (
        ArkhamEventParser()
        .parse(
            build_payload()
        )
    )

    assert isinstance(
        event,
        ArkhamWhaleEvent,
    )

    assert (
        event.event_id
        == "tx-001"
    )

    assert (
        event.asset
        == "ETH"
    )

    assert (
        event.amount_usd
        == 30000000
    )


def test_parser_normalizes_timestamp():

    event = (
        ArkhamEventParser()
        .parse(
            build_payload()
        )
    )

    assert (
        event.observed_at.tzinfo
        is not None
    )


def test_invalid_payload_rejected():

    with pytest.raises(TypeError):

        ArkhamEventParser().parse(
            "bad"
        )
