from datetime import datetime, timezone

from app.intelligence.early_bird.rank_transition_memory import (
    CandidateRankTransitionMemory,
)


NOW = datetime(
    2026,
    8,
    2,
    21,
    0,
    tzinfo=timezone.utc,
)


def test_rank_transition_memory_contract():

    memory = CandidateRankTransitionMemory(
        asset="HYPE",
        previous_rank="L4",
        current_rank="S3",
        transition_type="REVERSAL",
        reason=(
            "bullish exhaustion changed "
            "directional bias"
        ),
        timestamp=NOW,
    )

    assert memory.asset == "HYPE"
    assert memory.previous_rank == "L4"
    assert memory.current_rank == "S3"
    assert memory.transition_type == "REVERSAL"


def test_invalid_transition_type_rejected():

    try:
        CandidateRankTransitionMemory(
            asset="BTC",
            previous_rank="L2",
            current_rank="L3",
            transition_type="UNKNOWN",
            reason="invalid",
            timestamp=NOW,
        )

    except ValueError as exc:
        assert "transition" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
