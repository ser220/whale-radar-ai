from app.intelligence.early_bird.perpetual_opportunity import (
    PerpetualOpportunity,
)

from app.intelligence.early_bird.execution_readiness_evaluator import (
    ExecutionReadinessEvaluator,
)


def test_high_risk_blocks_perpetual_execution():

    opportunity = PerpetualOpportunity(
        asset="SOL",
        direction="SHORT",
        setup_type="REVERSAL",
        rank="R4",
        score=95,
        priority=100,
        confidence=95,
        reason="strong reversal signal",
    )


    readiness = ExecutionReadinessEvaluator().evaluate(
        opportunity,
        risk_score=85,
        news_risk=80,
    )


    assert readiness.asset == "SOL"
    assert readiness.direction == "SHORT"
    assert readiness.status == "WAIT"
    assert (
        "risk"
        in readiness.reason
        or
        "uncertainty"
        in readiness.reason
    )
