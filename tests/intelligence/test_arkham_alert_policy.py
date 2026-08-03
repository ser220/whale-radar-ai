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

from app.intelligence.arkham.alert_policy import (
    ArkhamAlertPolicy,
)


def build_event(amount):

    return ArkhamWhaleEvent(
        event_id="alert-test",
        chain=ArkhamChain.ETHEREUM,
        event_type=ArkhamEventType.WHALE_TRANSFER,
        direction=ArkhamFlowDirection.OUTFLOW,
        asset="ETH",
        amount_usd=amount,
        source_entity="Binance",
        destination_entity="Whale Wallet",
        observed_at=datetime.now(
            timezone.utc
        ),
    )


def test_large_whale_event_creates_alert():

    result = (
        ArkhamAlertPolicy()
        .evaluate(
            build_event(15000000)
        )
    )

    assert result is True


def test_small_transfer_ignored():

    result = (
        ArkhamAlertPolicy()
        .evaluate(
            build_event(500000)
        )
    )

    assert result is False


def test_invalid_event():

    with pytest.raises(TypeError):

        ArkhamAlertPolicy().evaluate(
            "bad"
        )
