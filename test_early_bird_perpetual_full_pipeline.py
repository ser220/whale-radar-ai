from app.intelligence.early_bird.directional_analyzer import (
    DirectionalAnalyzer,
)

from app.intelligence.early_bird.news_impact_aggregator import (
    NewsImpactAggregator,
)

from app.intelligence.early_bird.candidate_news_risk import (
    CandidateNewsRisk,
)

from app.intelligence.early_bird.perpetual_direction_resolver import (
    PerpetualDirectionResolver,
)

from app.intelligence.early_bird.perpetual_opportunity import (
    PerpetualOpportunity,
)

from app.intelligence.early_bird.perpetual_position_builder import (
    PerpetualPositionBuilder,
)

from app.intelligence.early_bird.position_risk_planner import (
    PositionRiskPlanner,
)

from app.intelligence.early_bird.perpetual_order_builder import (
    PerpetualOrderBuilder,
)

from app.intelligence.early_bird.perpetual_execution_request_builder import (
    PerpetualExecutionRequestBuilder,
)


def test_full_perpetual_pipeline():

    signals = {
        "momentum": 100,
        "volume": 100,
        "oi_health": 100,
        "exhaustion": 0,
        "bearish_structure": 0,
    }

    directional = DirectionalAnalyzer().analyze(
        signals
    )

    directional = directional.__class__(
        asset="HYPE",
        long_score=directional.long_score,
        short_score=directional.short_score,
        long_rank=directional.long_rank,
        short_rank=directional.short_rank,
        market_regime=directional.market_regime,
        confidence=directional.confidence,
    )

    news = CandidateNewsRisk(
        asset="HYPE",
        news_pressure_score=10,
        event_type="none",
        directional_bias="bullish",
        uncertainty_score=10,
    )

    adjusted = NewsImpactAggregator().apply(
        directional,
        news,
    )

    decision = PerpetualDirectionResolver().resolve(
        adjusted,
        market_regime=directional.market_regime,
    )

    assert decision.direction == "LONG"


    opportunity = PerpetualOpportunity(
        asset="HYPE",
        direction=decision.direction,
        setup_type="CONTINUATION",
        rank="L3",
        score=adjusted.confidence,
        priority=adjusted.confidence,
        confidence=adjusted.confidence,
        reason="pipeline test",
    )


    position = PerpetualPositionBuilder().build(
        opportunity
    )

    risk_plan = PositionRiskPlanner().plan(
        position,
        confidence=opportunity.confidence,
        risk_score=20,
        news_risk=10,
        setup_type=opportunity.setup_type,
    )

    order = PerpetualOrderBuilder().build(
        risk_plan
    )

    request = PerpetualExecutionRequestBuilder().build(
        order,
        exchange="OKX",
    )


    assert request.asset == "HYPE"
    assert request.direction == "LONG"
    assert request.exchange == "OKX"
    assert request.leverage > 0
