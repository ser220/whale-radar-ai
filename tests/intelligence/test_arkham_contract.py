from datetime import datetime, timezone

import pytest

from app.intelligence.arkham.models import (
    ArkhamWhaleEvent,
)

from app.intelligence.arkham.enums import (
    ArkhamChain,
    ArkhamEventType,
    ArkhamFlowDirection,
)


def build_event() -> ArkhamWhaleEvent:
    return ArkhamWhaleEvent(
        event_id="arkham-001",
        chain=ArkhamChain.ETHEREUM,
        event_type=ArkhamEventType.CEX_WITHDRAWAL,
        direction=ArkhamFlowDirection.OUTFLOW,
        asset="ETH",
        amount_usd=21000000,
        source_entity="Binance",
        destination_entity="Unknown Wallet",
        observed_at=datetime.now(
            timezone.utc
        ),
    )


def test_arkham_event_contract():

    event = build_event()

    assert event.event_id == "arkham-001"
    assert event.asset == "ETH"
    assert event.chain == ArkhamChain.ETHEREUM
    assert (
        event.event_type
        == ArkhamEventType.CEX_WITHDRAWAL
    )
    assert (
        event.direction
        == ArkhamFlowDirection.OUTFLOW
    )


def test_event_timestamp_is_utc():

    event = build_event()

    assert (
        event.observed_at.tzinfo
        is not None
    )


def test_invalid_event_rejected():

    with pytest.raises(ValueError):

        ArkhamWhaleEvent(
            event_id="",
            chain=ArkhamChain.ETHEREUM,
            event_type=ArkhamEventType.WHALE_TRANSFER,
            direction=ArkhamFlowDirection.OUTFLOW,
            asset="ETH",
            amount_usd=100,
            source_entity="A",
            destination_entity="B",
            observed_at=datetime.now(
                timezone.utc
            ),
        )
