from app.intelligence.early_bird.perpetual_execution_readiness import (
    PerpetualExecutionReadiness,
)

from app.intelligence.early_bird.execution_decision import (
    ExecutionDecision,
)


def test_ready_generates_open():

    readiness = PerpetualExecutionReadiness(
        asset="HYPE",
        direction="SHORT",
        status="READY",
        confidence=92.0,
        risk_score=20.0,
        news_risk=15.0,
        reason="reversal confirmed",
    )

    result = ExecutionDecision().evaluate(
        readiness
    )

    assert result.action == "OPEN"
    assert result.direction == "SHORT"



def test_wait_generates_wait():

    readiness = PerpetualExecutionReadiness(
        asset="BTC",
        direction="LONG",
        status="WAIT",
        confidence=80.0,
        risk_score=20.0,
        news_risk=90.0,
        reason="news uncertainty",
    )

    result = ExecutionDecision().evaluate(
        readiness
    )

    assert result.action == "WAIT"
