from app.intelligence.early_bird.candidate_dual_rank import (
    CandidateDualRank,
)

from app.intelligence.early_bird.candidate_dual_rank_lifecycle import (
    CandidateDualRankLifecycle,
)

from app.intelligence.early_bird.dual_rank_lifecycle_updater import (
    DualRankLifecycleUpdater,
)


def test_updates_long_to_reversal():

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

    new_rank = CandidateDualRank(
        asset="HYPE",
        long_rank="L2",
        short_rank="S4",
        long_score=55.0,
        short_score=85.0,
        transition_state="SHORT_DOMINANT",
    )

    updated = DualRankLifecycleUpdater().update(
        lifecycle,
        new_rank,
    )

    assert updated.current_state == (
        "REVERSAL_CONFIRMED"
    )

    assert updated.highest_long_rank == "L4"
    assert updated.highest_short_rank == "S4"



def test_updates_promotion():

    lifecycle = CandidateDualRankLifecycle(
        asset="SOL",
        current_long_rank="L2",
        current_short_rank="S1",
        highest_long_rank="L2",
        highest_short_rank="S1",
        current_state="LONG_DOMINANT",
        transition_history=(),
    )

    new_rank = CandidateDualRank(
        asset="SOL",
        long_rank="L3",
        short_rank="S1",
        long_score=70.0,
        short_score=20.0,
        transition_state="LONG_DOMINANT",
    )

    updated = DualRankLifecycleUpdater().update(
        lifecycle,
        new_rank,
    )

    assert updated.current_long_rank == "L3"
    assert "PROMOTION" in updated.transition_history
