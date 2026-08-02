from app.intelligence.early_bird.perpetual_execution_request import (
    PerpetualExecutionRequest,
)


def test_execution_request_contract():

    request = PerpetualExecutionRequest(
        asset="HYPE",
        direction="SHORT",
        order_type="LIMIT",
        size=30.0,
        leverage=3,
        exchange="OKX",
        client_reference="wr-058m-test",
    )

    assert request.asset == "HYPE"
    assert request.direction == "SHORT"
    assert request.exchange == "OKX"
    assert request.leverage == 3



def test_invalid_exchange():

    try:

        PerpetualExecutionRequest(
            asset="BTC",
            direction="LONG",
            order_type="MARKET",
            size=50.0,
            leverage=5,
            exchange="",
            client_reference="test",
        )

    except ValueError as exc:
        assert "exchange" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
