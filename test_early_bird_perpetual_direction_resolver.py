from app.intelligence.early_bird.news_impact_aggregator import (
    CandidateAdjustedDirectionScore,
)

from app.intelligence.early_bird.perpetual_direction_resolver import (
    PerpetualDirectionResolver,
)


def test_resolver_selects_long_continuation():

    score = CandidateAdjustedDirectionScore(
        asset="SOL",
        adjusted_long_score=85.0,
        adjusted_short_score=25.0,
        uncertainty_level=15.0,
        confidence=85.0,
    )

    result = PerpetualDirectionResolver().resolve(
        score
    )

    assert result.direction == "LONG"
    assert result.confidence > 70


def test_resolver_selects_short_reversal():

    score = CandidateAdjustedDirectionScore(
        asset="HYPE",
        adjusted_long_score=58.0,
        adjusted_short_score=86.0,
        uncertainty_level=20.0,
        confidence=86.0,
    )

    result = PerpetualDirectionResolver().resolve(
        score,
        market_regime="bullish_exhaustion",
    )

    assert result.direction == "SHORT"


def test_resolver_waits_when_uncertain():

    score = CandidateAdjustedDirectionScore(
        asset="BTC",
        adjusted_long_score=62.0,
        adjusted_short_score=60.0,
        uncertainty_level=85.0,
        confidence=40.0,
    )

    result = PerpetualDirectionResolver().resolve(
        score,
    )

    assert result.direction == "WAIT"
