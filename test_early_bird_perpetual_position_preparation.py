from app.intelligence.early_bird.perpetual_position_preparation import (
    PerpetualPositionPreparation,
)


def test_position_preparation_contract():

    position = PerpetualPositionPreparation(
        asset="HYPE",
        direction="SHORT",
        entry_mode="LIMIT",
        risk_allocation=5.0,
        leverage_limit=3,
        dca_allowed=False,
        reason="reversal risk controlled",
    )

    assert position.asset == "HYPE"
    assert position.direction == "SHORT"
    assert position.entry_mode == "LIMIT"
    assert position.dca_allowed is False



def test_invalid_leverage():

    try:

        PerpetualPositionPreparation(
            asset="BTC",
            direction="LONG",
            entry_mode="MARKET",
            risk_allocation=5.0,
            leverage_limit=0,
            dca_allowed=True,
            reason="test",
        )

    except ValueError as exc:
        assert "leverage" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
