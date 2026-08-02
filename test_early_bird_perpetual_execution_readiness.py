from app.intelligence.early_bird.perpetual_execution_readiness import (
    PerpetualExecutionReadiness,
)


def test_execution_readiness_contract():

    result = PerpetualExecutionReadiness(
        asset="HYPE",
        direction="SHORT",
        status="READY",
        confidence=92.0,
        risk_score=20.0,
        news_risk=15.0,
        reason=(
            "reversal confirmed"
        ),
    )

    assert result.asset == "HYPE"
    assert result.direction == "SHORT"
    assert result.status == "READY"
    assert result.confidence == 92.0



def test_invalid_status():

    try:

        PerpetualExecutionReadiness(
            asset="BTC",
            direction="LONG",
            status="UNKNOWN",
            confidence=80.0,
            risk_score=20.0,
            news_risk=10.0,
            reason="test",
        )

    except ValueError as exc:
        assert "status" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
