from app.intelligence.early_bird.perpetual_opportunity import (
    PerpetualOpportunity,
)

from app.intelligence.early_bird.execution_readiness_evaluator import (
    ExecutionReadinessEvaluator,
)

from app.intelligence.early_bird.perpetual_position_preparation import (
    PerpetualPositionPreparation,
)

from app.intelligence.early_bird.position_risk_planner import (
    PositionRiskPlanner,
)


def test_opportunity_flows_into_execution_gate_and_risk():

    opportunity = PerpetualOpportunity(
        asset="SOL",
        direction="SHORT",
        setup_type="REVERSAL",
        rank="R4",
        score=90,
        priority=95,
        confidence=90,
        reason="major reversal detected",
    )


    readiness = ExecutionReadinessEvaluator().evaluate(
        opportunity,
        risk_score=20,
        news_risk=10,
    )


    assert readiness.asset == "SOL"
    assert readiness.direction == "SHORT"
    assert readiness.status == "READY"


    preparation = PerpetualPositionPreparation(
        asset=readiness.asset,
        direction=readiness.direction,
        entry_mode="LIMIT",
        risk_allocation=5.0,
        leverage_limit=5,
        dca_allowed=True,
        reason="controlled reversal entry",
    )


    risk_plan = PositionRiskPlanner().plan(
        preparation,
        confidence=readiness.confidence,
        risk_score=readiness.risk_score,
        news_risk=readiness.news_risk,
        setup_type=opportunity.setup_type,
    )


    assert risk_plan.asset == "SOL"
    assert risk_plan.direction == "SHORT"
    assert risk_plan.max_leverage <= 3
