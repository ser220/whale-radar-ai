from app.intelligence.early_bird.candidate_dual_rank_lifecycle import (
    CandidateDualRankLifecycle,
)


def test_dual_rank_lifecycle_contract():

    lifecycle = CandidateDualRankLifecycle(
        asset="HYPE",
        current_long_rank="L2",
        current_short_rank="S4",
        highest_long_rank="L4",
        highest_short_rank="S4",
        current_state="REVERSAL_CONFIRMED",
        transition_history=(
            "PROMOTION",
            "REVERSAL",
        ),
    )

    assert lifecycle.asset == "HYPE"
    assert lifecycle.current_long_rank == "L2"
    assert lifecycle.current_short_rank == "S4"
    assert lifecycle.highest_long_rank == "L4"
    assert lifecycle.current_state == (
        "REVERSAL_CONFIRMED"
    )


def test_invalid_state_rejected():

    try:
        CandidateDualRankLifecycle(
            asset="BTC",
            current_long_rank="L1",
            current_short_rank="S1",
            highest_long_rank="L1",
            highest_short_rank="S1",
            current_state="UNKNOWN",
            transition_history=(),
        )

    except ValueError as exc:
        assert "state" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
