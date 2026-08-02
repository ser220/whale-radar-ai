from datetime import datetime, timezone

from app.intelligence.early_bird.candidate_ranking_record import (
    CandidateRankingRecord,
)

from app.intelligence.early_bird.candidate_leaderboard import (
    CandidateLeaderboard,
)

from app.intelligence.early_bird.perpetual_opportunity_selector import (
    PerpetualOpportunitySelector,
)


def test_reversal_pool_overrides_long_leader():

    leaderboard = CandidateLeaderboard(
        long_candidates=(
            CandidateRankingRecord(
                asset="HYPE",
                direction="LONG",
                rank="L4",
                score=85,
                confidence=85,
                risk_score=30,
                priority=85,
            ),
        ),

        short_candidates=(),

        reversal_candidates=(
            CandidateRankingRecord(
                asset="HYPE",
                direction="REVERSAL",
                rank="R4",
                score=90,
                confidence=90,
                risk_score=25,
                priority=95,
            ),
        ),

        timestamp=datetime.now(
            timezone.utc
        ),
    )


    opportunity = PerpetualOpportunitySelector().select(
        leaderboard
    )


    assert opportunity.asset == "HYPE"
    assert opportunity.direction == "SHORT"
    assert opportunity.setup_type == "REVERSAL"
