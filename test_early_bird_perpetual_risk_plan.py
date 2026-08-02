from app.intelligence.early_bird.perpetual_risk_plan import (
    PerpetualRiskPlan,
)


def test_risk_plan_contract():

    plan = PerpetualRiskPlan(
        asset="HYPE",
        direction="SHORT",
        risk_mode="REDUCED",
        max_position_risk=2.0,
        initial_order_size=30.0,
        dca_budget=10.0,
        max_leverage=3,
    )

    assert plan.asset == "HYPE"
    assert plan.direction == "SHORT"
    assert plan.risk_mode == "REDUCED"
    assert plan.max_leverage == 3



def test_invalid_risk_mode():

    try:
        PerpetualRiskPlan(
            asset="BTC",
            direction="LONG",
            risk_mode="UNKNOWN",
            max_position_risk=5.0,
            initial_order_size=50.0,
            dca_budget=20.0,
            max_leverage=5,
        )

    except ValueError as exc:
        assert "risk_mode" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
