from app.intelligence.early_bird.candidate_dual_rank import (
    CandidateDualRank,
)

from app.intelligence.early_bird.candidate_dual_rank_lifecycle import (
    CandidateDualRankLifecycle,
)

from app.intelligence.early_bird.dual_rank_lifecycle_updater import (
    DualRankLifecycleUpdater,
)


def test_long_to_short_reversal_lifecycle():

    lifecycle = CandidateDualRankLifecycle(
        asset="HYPE",
        current_long_rank="L4",
        current_short_rank="S1",
        highest_long_rank="L4",
        highest_short_rank="S1",
        current_state="LONG_DOMINANT",
        transition_history=(
            "PROMOTION",
        ),
    )

    reversal_rank = CandidateDualRank(
        asset="HYPE",
        long_rank="L2",
        short_rank="S4",
        long_score=55.0,
        short_score=88.0,
        transition_state="SHORT_DOMINANT",
    )

    updated = DualRankLifecycleUpdater().update(
        lifecycle,
        reversal_rank,
    )

    assert updated.current_state == (
        "REVERSAL_CONFIRMED"
    )

    assert updated.current_long_rank == "L2"
    assert updated.current_short_rank == "S4"

    assert updated.highest_long_rank == "L4"
    assert updated.highest_short_rank == "S4"

    assert (
        "REVERSAL"
        in
        updated.transition_history
    )


def test_long_growth_keeps_history():

    lifecycle = CandidateDualRankLifecycle(
        asset="SOL",
        current_long_rank="L2",
        current_short_rank="S1",
        highest_long_rank="L2",
        highest_short_rank="S1",
        current_state="LONG_DOMINANT",
        transition_history=(),
    )

    next_rank = CandidateDualRank(
        asset="SOL",
        long_rank="L4",
        short_rank="S1",
        long_score=90.0,
        short_score=20.0,
        transition_state="LONG_DOMINANT",
    )

    updated = DualRankLifecycleUpdater().update(
        lifecycle,
        next_rank,
    )

    assert updated.current_long_rank == "L4"
    assert updated.highest_long_rank == "L4"
    assert (
        updated.current_state
        ==
        "LONG_DOMINANT"
    )
