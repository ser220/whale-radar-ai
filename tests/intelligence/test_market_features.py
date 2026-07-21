from datetime import datetime, timezone

import pytest

from app.intelligence.market import (
    MarketSnapshot,
)
from app.intelligence.features import (
    MarketFeatureExtractor,
    MarketFeatures,
)


def build_snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        symbol="BTCUSDT",
        price=65000.0,
        volume_24h=1000000000.0,
        volatility=0.035,
        captured_at=datetime.now(
            timezone.utc
        ),
    )


def test_extract_market_features():
    snapshot = build_snapshot()

    features = (
        MarketFeatureExtractor
        .extract(snapshot)
    )

    assert isinstance(
        features,
        MarketFeatures,
    )

    assert (
        features.symbol
        == "BTCUSDT"
    )

    assert (
        features.trend
        == "bullish"
    )

    assert (
        features.volatility_state
        == "normal"
    )

    assert (
        features.liquidity_state
        == "healthy"
    )


def test_high_volatility_detection():
    snapshot = MarketSnapshot(
        symbol="BTCUSDT",
        price=65000.0,
        volume_24h=1000000000.0,
        volatility=0.08,
        captured_at=datetime.now(
            timezone.utc
        ),
    )

    features = (
        MarketFeatureExtractor
        .extract(snapshot)
    )

    assert (
        features.volatility_state
        == "high"
    )


def test_invalid_input_rejected():
    with pytest.raises(TypeError):
        MarketFeatureExtractor.extract(
            "invalid"
        )
