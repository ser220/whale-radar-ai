from app.intelligence.early_bird.perpetual_opportunity import (
    PerpetualOpportunity,
)

from app.intelligence.early_bird.execution_readiness_evaluator import (
    ExecutionReadinessEvaluator,
)


def test_ready_reversal_candidate():

    opportunity = PerpetualOpportunity(
        asset="HYPE",
        direction="SHORT",
        setup_type="REVERSAL",
        rank="S4",
        score=95.0,
        priority=99.0,
        confidence=90.0,
        reason="former long leader reversal",
    )

    result = ExecutionReadinessEvaluator().evaluate(
        opportunity,
        risk_score=20.0,
        news_risk=15.0,
    )

    assert result.status == "READY"
    assert result.direction == "SHORT"



def test_high_news_risk_wait():

    opportunity = PerpetualOpportunity(
        asset="BTC",
        direction="LONG",
        setup_type="CONTINUATION",
        rank="L4",
        score=90.0,
        priority=90.0,
        confidence=85.0,
        reason="trend continuation",
    )

    result = ExecutionReadinessEvaluator().evaluate(
        opportunity,
        risk_score=20.0,
        news_risk=90.0,
    )

    assert result.status == "WAIT"
