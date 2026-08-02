from app.intelligence.early_bird.execution_adapter import (
    PerpetualExecutionAdapter,
    PerpetualExecutionResult,
)


def test_execution_result_contract():

    result = PerpetualExecutionResult(
        status="SUBMITTED",
        exchange="OKX",
        order_id="abc123",
        asset="HYPE",
        direction="SHORT",
        filled_size=0.0,
        message="order accepted",
    )

    assert result.status == "SUBMITTED"
    assert result.exchange == "OKX"
    assert result.order_id == "abc123"



def test_adapter_interface():

    adapter = PerpetualExecutionAdapter()

    try:
        adapter.submit(None)

    except NotImplementedError:
        assert True

    else:
        raise AssertionError(
            "Expected NotImplementedError"
        )
