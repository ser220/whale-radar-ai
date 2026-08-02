from datetime import datetime, timezone

from app.intelligence.early_bird.candidate_leaderboard import (
    CandidateLeaderboard,
)

from app.intelligence.early_bird.candidate_ranking_record import (
    CandidateRankingRecord,
)

from app.intelligence.early_bird.perpetual_opportunity_selector import (
    PerpetualOpportunitySelector,
)


NOW = datetime(2026, 8, 2, 22, 30, tzinfo=timezone.utc)


def test_reversal_has_priority():

    leaderboard = CandidateLeaderboard(
        long_candidates=(
            CandidateRankingRecord(
                asset="SOL",
                direction="LONG",
                rank="L4",
                score=90.0,
                confidence=90.0,
                risk_score=20.0,
                priority=92.0,
            ),
        ),
        short_candidates=(
            CandidateRankingRecord(
                asset="AVAX",
                direction="SHORT",
                rank="S4",
                score=91.0,
                confidence=88.0,
                risk_score=25.0,
                priority=93.0,
            ),
        ),
        reversal_candidates=(
            CandidateRankingRecord(
                asset="HYPE",
                direction="REVERSAL",
                rank="S4",
                score=88.0,
                confidence=92.0,
                risk_score=20.0,
                priority=99.0,
            ),
        ),
        timestamp=NOW,
    )

    result = PerpetualOpportunitySelector().select(
        leaderboard
    )

    assert result.asset == "HYPE"
    assert result.direction == "SHORT"
    assert result.setup_type == "REVERSAL"



def test_returns_none_when_empty():

    leaderboard = CandidateLeaderboard(
        long_candidates=(),
        short_candidates=(),
        reversal_candidates=(),
        timestamp=NOW,
    )

    result = PerpetualOpportunitySelector().select(
        leaderboard
    )

    assert result is None
