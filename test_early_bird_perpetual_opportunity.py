from app.intelligence.early_bird.perpetual_opportunity import (
    PerpetualOpportunity,
)


def test_perpetual_opportunity_contract():

    opportunity = PerpetualOpportunity(
        asset="HYPE",
        direction="SHORT",
        setup_type="REVERSAL",
        rank="S4",
        score=95.0,
        priority=99.0,
        confidence=92.0,
        reason=(
            "former long leader "
            "reversed bearish"
        ),
    )

    assert opportunity.asset == "HYPE"
    assert opportunity.direction == "SHORT"
    assert opportunity.setup_type == "REVERSAL"
    assert opportunity.rank == "S4"
    assert opportunity.priority == 99.0



def test_invalid_direction():

    try:
        PerpetualOpportunity(
            asset="BTC",
            direction="UNKNOWN",
            setup_type="NORMAL",
            rank="L1",
            score=50.0,
            priority=50.0,
            confidence=50.0,
            reason="test",
        )

    except ValueError as exc:
        assert "direction" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
