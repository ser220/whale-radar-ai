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

from app.intelligence.arkham.store import (
    ArkhamEventStore,
)


def build_event(
    event_id="event-001",
):

    return ArkhamWhaleEvent(
        event_id=event_id,
        chain=ArkhamChain.ETHEREUM,
        event_type=ArkhamEventType.WHALE_TRANSFER,
        direction=ArkhamFlowDirection.OUTFLOW,
        asset="ETH",
        amount_usd=25000000,
        source_entity="Binance",
        destination_entity="Whale Wallet",
        observed_at=datetime.now(
            timezone.utc
        ),
    )


def test_event_store_saves_and_reads():

    store = ArkhamEventStore()

    event = build_event()

    store.save(event)

    loaded = store.get(
        "event-001"
    )

    assert loaded == event


def test_event_store_keeps_multiple_events():

    store = ArkhamEventStore()

    store.save(
        build_event("event-001")
    )

    store.save(
        build_event("event-002")
    )

    assert len(
        store.all()
    ) == 2


def test_invalid_event_rejected():

    store = ArkhamEventStore()

    with pytest.raises(TypeError):

        store.save(
            "bad"
        )
