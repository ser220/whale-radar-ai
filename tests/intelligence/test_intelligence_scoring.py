from datetime import datetime, timezone

import pytest

from app.intelligence.market import (
    MarketSnapshot,
)
from app.intelligence.features import (
    MarketFeatureExtractor,
)
from app.intelligence.scoring import (
    IntelligenceScore,
    IntelligenceScorer,
)


def build_features():
    snapshot = MarketSnapshot(
        symbol="BTCUSDT",
        price=65000.0,
        volume_24h=1000000000.0,
        volatility=0.035,
        captured_at=datetime.now(
            timezone.utc
        ),
    )

    return (
        MarketFeatureExtractor
        .extract(snapshot)
    )


def test_intelligence_score_creation():
    score = IntelligenceScore(
        symbol="BTCUSDT",
        score=85.0,
        confidence=0.85,
    )

    assert (
        score.symbol
        == "BTCUSDT"
    )

    assert (
        score.score
        == 85.0
    )

    assert (
        score.confidence
        == 0.85
    )


def test_scorer_generates_score():
    features = build_features()

    result = (
        IntelligenceScorer
        .score(features)
    )

    assert isinstance(
        result,
        IntelligenceScore,
    )

    assert (
        result.symbol
        == "BTCUSDT"
    )

    assert (
        result.score
        == 100.0
    )

    assert (
        result.confidence
        == 1.0
    )


def test_invalid_score_rejected():
    with pytest.raises(ValueError):
        IntelligenceScore(
            symbol="BTCUSDT",
            score=120,
            confidence=1.2,
        )


def test_invalid_input_rejected():
    with pytest.raises(TypeError):
        IntelligenceScorer.score(
            "invalid"
        )
