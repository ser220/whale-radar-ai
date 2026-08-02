from datetime import datetime, timezone

from app.intelligence.early_bird.candidate_ranking_record import (
    CandidateRankingRecord,
)

from app.intelligence.early_bird.candidate_leaderboard import (
    CandidateLeaderboard,
)


NOW = datetime(
    2026,
    8,
    2,
    22,
    0,
    tzinfo=timezone.utc,
)


def test_candidate_leaderboard_contract():

    long_candidate = CandidateRankingRecord(
        asset="SOL",
        direction="LONG",
        rank="L4",
        score=92.0,
        confidence=90.0,
        risk_score=20.0,
        priority=90.0,
    )

    reversal_candidate = CandidateRankingRecord(
        asset="HYPE",
        direction="REVERSAL",
        rank="S4",
        score=95.0,
        confidence=92.0,
        risk_score=25.0,
        priority=99.0,
    )

    leaderboard = CandidateLeaderboard(
        long_candidates=(
            long_candidate,
        ),
        short_candidates=(),
        reversal_candidates=(
            reversal_candidate,
        ),
        timestamp=NOW,
    )

    assert (
        leaderboard.long_candidates[0].asset
        ==
        "SOL"
    )

    assert (
        leaderboard.reversal_candidates[0].asset
        ==
        "HYPE"
    )


def test_leaderboard_requires_tuple():

    try:
        CandidateLeaderboard(
            long_candidates=[],
            short_candidates=(),
            reversal_candidates=(),
            timestamp=NOW,
        )

    except TypeError as exc:
        assert "tuple" in str(exc)

    else:
        raise AssertionError(
            "Expected TypeError"
        )
