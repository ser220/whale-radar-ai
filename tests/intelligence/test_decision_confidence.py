from datetime import datetime, timezone

import pytest

from app.intelligence.market import (
    MarketSnapshot,
)

from app.intelligence.features import (
    MarketFeatureExtractor,
)

from app.intelligence.scoring import (
    IntelligenceScorer,
)

from app.intelligence.risk import (
    RiskEvaluator,
)

from app.intelligence.confidence import (
    DecisionConfidence,
    ConfidenceAggregator,
)


def build_score_and_risk():
    snapshot = MarketSnapshot(
        symbol="BTCUSDT",
        price=65000.0,
        volume_24h=1000000000.0,
        volatility=0.035,
        captured_at=datetime.now(
            timezone.utc
        ),
    )

    features = (
        MarketFeatureExtractor
        .extract(snapshot)
    )

    score = (
        IntelligenceScorer
        .score(features)
    )

    risk = (
        RiskEvaluator
        .evaluate(
            features,
            score,
        )
    )

    return score, risk


def test_decision_confidence_creation():
    confidence = DecisionConfidence(
        symbol="BTCUSDT",
        confidence=0.75,
        level="high",
    )

    assert (
        confidence.symbol
        == "BTCUSDT"
    )

    assert (
        confidence.confidence
        == 0.75
    )

    assert (
        confidence.level
        == "high"
    )


def test_confidence_aggregation():
    score, risk = (
        build_score_and_risk()
    )

    result = (
        ConfidenceAggregator
        .aggregate(
            score,
            risk,
        )
    )

    assert isinstance(
        result,
        DecisionConfidence,
    )

    assert (
        result.symbol
        == "BTCUSDT"
    )

    assert (
        result.confidence
        > 0
    )


def test_high_risk_reduces_confidence():
    score, risk = (
        build_score_and_risk()
    )

    reduced_risk = type(risk)(
        symbol=risk.symbol,
        risk_level="high",
        risk_score=90,
        reasons=(
            "high volatility",
        ),
    )

    result = (
        ConfidenceAggregator
        .aggregate(
            score,
            reduced_risk,
        )
    )

    assert (
        result.confidence
        <
        score.confidence
    )


def test_invalid_input_rejected():
    with pytest.raises(TypeError):
        ConfidenceAggregator.aggregate(
            "invalid",
            "invalid",
        )
