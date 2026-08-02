from app.intelligence.early_bird.candidate_directional_score import (
    CandidateDirectionalScore,
)

from app.intelligence.early_bird.candidate_news_risk import (
    CandidateNewsRisk,
)

from app.intelligence.early_bird.news_impact_aggregator import (
    NewsImpactAggregator,
)


def test_negative_news_reduces_long_confidence():

    directional = CandidateDirectionalScore(
        asset="HYPE",
        long_score=85.0,
        short_score=25.0,
        long_rank="L4",
        short_rank="S1",
        market_regime="bullish_continuation",
        confidence=90.0,
    )

    news = CandidateNewsRisk(
        asset="HYPE",
        news_pressure_score=80.0,
        event_type="token_unlock",
        directional_bias="bearish",
        uncertainty_score=85.0,
    )

    result = NewsImpactAggregator().apply(
        directional,
        news,
    )

    assert result.adjusted_long_score < 85.0
    assert result.uncertainty_level > 50


def test_positive_news_supports_long():

    directional = CandidateDirectionalScore(
        asset="SOL",
        long_score=70.0,
        short_score=20.0,
        long_rank="L3",
        short_rank="S1",
        market_regime="bullish_continuation",
        confidence=75.0,
    )

    news = CandidateNewsRisk(
        asset="SOL",
        news_pressure_score=70.0,
        event_type="positive_listing",
        directional_bias="bullish",
        uncertainty_score=20.0,
    )

    result = NewsImpactAggregator().apply(
        directional,
        news,
    )

    assert result.adjusted_long_score > 70.0
