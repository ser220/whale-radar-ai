from app.intelligence.early_bird.rank_cascade_engine import (
    RankCascadeEngine,
)


def test_long_rank_cascade():

    result = RankCascadeEngine().evaluate(
        asset="HYPE",
        long_score=85.0,
        short_score=20.0,
    )

    assert result.long_rank == "L4"
    assert result.short_rank == "S1"
    assert (
        result.transition_state
        ==
        "LONG_DOMINANT"
    )


def test_short_rank_cascade_after_reversal():

    result = RankCascadeEngine().evaluate(
        asset="HYPE",
        long_score=55.0,
        short_score=88.0,
    )

    assert result.long_rank == "L2"
    assert result.short_rank == "S4"
    assert (
        result.transition_state
        ==
        "SHORT_DOMINANT"
    )


def test_transition_zone():

    result = RankCascadeEngine().evaluate(
        asset="BTC",
        long_score=62.0,
        short_score=60.0,
    )

    assert (
        result.transition_state
        ==
        "TRANSITION"
    )
