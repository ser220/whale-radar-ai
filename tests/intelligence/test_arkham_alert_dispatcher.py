import pytest

from datetime import datetime, timezone

from app.intelligence.arkham.alert_dispatcher import (
    ArkhamAlertDispatcher,
)

from app.intelligence.arkham.models import (
    ArkhamWhaleEvent,
)

from app.intelligence.arkham.enums import (
    ArkhamChain,
    ArkhamEventType,
    ArkhamFlowDirection,
)


def build_event():

    return ArkhamWhaleEvent(
        event_id="alert-001",
        chain=ArkhamChain.ETHEREUM,
        event_type=ArkhamEventType.WHALE_TRANSFER,
        direction=ArkhamFlowDirection.OUTFLOW,
        asset="ETH",
        amount_usd=50000000,
        source_entity="Binance",
        destination_entity="Whale Wallet",
        observed_at=datetime.now(
            timezone.utc
        ),
    )


def test_dispatcher_stores_alert():

    dispatcher = ArkhamAlertDispatcher()

    event = build_event()

    dispatcher.dispatch(event)

    sent = dispatcher.sent_events()

    assert len(sent) == 1

    assert (
        sent[0].event_id
        == "alert-001"
    )


def test_invalid_event_rejected():

    dispatcher = ArkhamAlertDispatcher()

    with pytest.raises(TypeError):

        dispatcher.dispatch(
            "bad"
        )
