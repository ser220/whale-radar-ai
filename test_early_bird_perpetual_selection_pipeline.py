from datetime import datetime, timezone

from app.intelligence.early_bird.perpetual_opportunity_selector import (
    PerpetualOpportunitySelector,
)

from app.intelligence.early_bird.candidate_leaderboard import (
    CandidateLeaderboard,
)

from app.intelligence.early_bird.candidate_ranking_record import (
    CandidateRankingRecord,
)


def test_leaderboard_selects_perpetual_opportunity():

    leaderboard = CandidateLeaderboard(
        long_candidates=(
            CandidateRankingRecord(
                asset="HYPE",
                direction="LONG",
                rank="L4",
                score=90,
                confidence=90,
                risk_score=20,
                priority=90,
            ),
        ),
        short_candidates=(),
        reversal_candidates=(),
        timestamp=datetime.now(timezone.utc),
    )

    result = PerpetualOpportunitySelector().select(
        leaderboard
    )

    assert result.asset == "HYPE"
    assert result.direction == "LONG"
