from app.intelligence.early_bird.perpetual_order_builder import (
    PerpetualOrderBuilder,
)

from app.intelligence.early_bird.perpetual_risk_plan import (
    PerpetualRiskPlan,
)


def test_order_builder_creates_order_preparation():

    risk_plan = PerpetualRiskPlan(
        asset="HYPE",
        direction="LONG",
        risk_mode="NORMAL",
        max_position_risk=5.0,
        initial_order_size=100.0,
        dca_budget=20.0,
        max_leverage=5,
    )

    result = PerpetualOrderBuilder().build(
        risk_plan,
    )

    assert result.asset == "HYPE"
    assert result.direction == "LONG"
    assert result.order_type == "LIMIT"
    assert result.entry_mode == "RETEST"
    assert result.dca_enabled is True
