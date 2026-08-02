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

from app.intelligence.early_bird.perpetual_order_builder import (
    PerpetualOrderBuilder,
)

from app.intelligence.early_bird.perpetual_execution_request_builder import (
    PerpetualExecutionRequestBuilder,
)


def test_full_perpetual_radar_execution_flow():

    opportunity = PerpetualOpportunity(
        asset="HYPE",
        direction="LONG",
        setup_type="CONTINUATION",
        rank="L4",
        score=90,
        priority=90,
        confidence=90,
        reason="strong continuation setup",
    )


    readiness = ExecutionReadinessEvaluator().evaluate(
        opportunity,
        risk_score=20,
        news_risk=10,
    )


    assert readiness.status == "READY"


    preparation = PerpetualPositionPreparation(
        asset=readiness.asset,
        direction=readiness.direction,
        entry_mode="LIMIT",
        risk_allocation=5.0,
        leverage_limit=5,
        dca_allowed=True,
        reason="controlled long entry",
    )


    risk_plan = PositionRiskPlanner().plan(
        preparation,
        confidence=readiness.confidence,
        risk_score=readiness.risk_score,
        news_risk=readiness.news_risk,
        setup_type=opportunity.setup_type,
    )


    order = PerpetualOrderBuilder().build(
        risk_plan,
    )


    request = PerpetualExecutionRequestBuilder().build(
        order,
        exchange="OKX",
    )


    assert request.asset == "HYPE"
    assert request.direction == "LONG"
    assert request.exchange == "OKX"
