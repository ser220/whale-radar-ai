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
    RiskAssessment,
    RiskEvaluator,
)


def build_features_and_score():
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

    return features, score


def test_risk_assessment_creation():
    assessment = RiskAssessment(
        symbol="BTCUSDT",
        risk_level="low",
        risk_score=20.0,
        reasons=(
            "healthy liquidity",
        ),
    )

    assert (
        assessment.symbol
        == "BTCUSDT"
    )

    assert (
        assessment.risk_level
        == "low"
    )

    assert (
        assessment.risk_score
        == 20.0
    )


def test_risk_evaluator_returns_assessment():
    features, score = (
        build_features_and_score()
    )

    result = (
        RiskEvaluator
        .evaluate(
            features,
            score,
        )
    )

    assert isinstance(
        result,
        RiskAssessment,
    )

    assert (
        result.symbol
        == "BTCUSDT"
    )

    assert (
        result.risk_level
        == "low"
    )


def test_high_volatility_increases_risk():
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

    score = (
        IntelligenceScorer
        .score(features)
    )

    result = (
        RiskEvaluator
        .evaluate(
            features,
            score,
        )
    )

    assert (
        result.risk_score
        > 50
    )

    assert (
        "high volatility"
        in result.reasons
    )


def test_invalid_input_rejected():
    with pytest.raises(TypeError):
        RiskEvaluator.evaluate(
            "invalid",
            "invalid",
        )
