from datetime import datetime, timezone

import pytest

from app.intelligence.market import (
    MarketIntelligenceAdapter,
    MarketSnapshot,
)


def test_market_snapshot_creation():
    snapshot = MarketSnapshot(
        symbol="BTCUSDT",
        price=65000.0,
        volume_24h=1000000000.0,
        volatility=0.035,
        captured_at=datetime.now(
            timezone.utc
        ),
    )

    assert (
        snapshot.symbol
        == "BTCUSDT"
    )

    assert (
        snapshot.price
        == 65000.0
    )

    assert (
        snapshot.volume_24h
        == 1000000000.0
    )


def test_adapter_creates_snapshot():
    adapter = MarketIntelligenceAdapter()

    snapshot = adapter.snapshot(
        symbol="ETHUSDT",
        price=3500.0,
        volume_24h=500000000.0,
        volatility=0.02,
    )

    assert isinstance(
        snapshot,
        MarketSnapshot,
    )

    assert (
        snapshot.symbol
        == "ETHUSDT"
    )


def test_empty_symbol_rejected():
    with pytest.raises(ValueError):
        MarketSnapshot(
            symbol="",
            price=100.0,
            volume_24h=1000.0,
            volatility=0.01,
            captured_at=datetime.now(
                timezone.utc
            ),
        )


def test_negative_price_rejected():
    with pytest.raises(ValueError):
        MarketSnapshot(
            symbol="BTCUSDT",
            price=-1,
            volume_24h=1000.0,
            volatility=0.01,
            captured_at=datetime.now(
                timezone.utc
            ),
        )
