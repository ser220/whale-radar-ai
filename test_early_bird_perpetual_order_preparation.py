from app.intelligence.early_bird.perpetual_order_preparation import (
    PerpetualOrderPreparation,
)


def test_order_preparation_contract():

    order = PerpetualOrderPreparation(
        asset="HYPE",
        direction="SHORT",
        order_type="LIMIT",
        entry_mode="RETEST",
        initial_size=30.0,
        leverage=3,
        dca_enabled=False,
        protection_mode="STRICT",
    )

    assert order.asset == "HYPE"
    assert order.direction == "SHORT"
    assert order.order_type == "LIMIT"
    assert order.leverage == 3
    assert order.dca_enabled is False



def test_invalid_order_type():

    try:

        PerpetualOrderPreparation(
            asset="BTC",
            direction="LONG",
            order_type="UNKNOWN",
            entry_mode="MARKET",
            initial_size=50.0,
            leverage=5,
            dca_enabled=True,
            protection_mode="NORMAL",
        )

    except ValueError as exc:
        assert "order_type" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
