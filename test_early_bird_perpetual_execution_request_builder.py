from app.intelligence.early_bird.perpetual_execution_request_builder import (
    PerpetualExecutionRequestBuilder,
)

from app.intelligence.early_bird.perpetual_order_preparation import (
    PerpetualOrderPreparation,
)


def test_execution_request_builder_creates_request():

    order = PerpetualOrderPreparation(
        asset="HYPE",
        direction="LONG",
        order_type="LIMIT",
        entry_mode="RETEST",
        initial_size=100.0,
        leverage=5,
        dca_enabled=True,
        protection_mode="NORMAL",
    )

    result = PerpetualExecutionRequestBuilder().build(
        order,
        exchange="OKX",
    )

    assert result.asset == "HYPE"
    assert result.direction == "LONG"
    assert result.exchange == "OKX"
    assert result.order_type == "LIMIT"
