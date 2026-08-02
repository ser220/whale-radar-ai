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


def test_global_candidate_priority_prefers_reversal():

    leaderboard = CandidateLeaderboard(

        long_candidates=(
            CandidateRankingRecord(
                asset="HYPE",
                direction="LONG",
                rank="L4",
                score=95,
                confidence=90,
                risk_score=20,
                priority=95,
            ),
            CandidateRankingRecord(
                asset="BTC",
                direction="LONG",
                rank="L3",
                score=75,
                confidence=80,
                risk_score=25,
                priority=75,
            ),
        ),

        short_candidates=(),

        reversal_candidates=(
            CandidateRankingRecord(
                asset="SOL",
                direction="REVERSAL",
                rank="R4",
                score=85,
                confidence=85,
                risk_score=30,
                priority=100,
            ),
        ),

        timestamp=datetime.now(
            timezone.utc
        ),
    )


    opportunity = (
        PerpetualOpportunitySelector()
        .select(
            leaderboard
        )
    )


    assert opportunity.asset == "SOL"
    assert opportunity.direction == "SHORT"
    assert opportunity.setup_type == "REVERSAL"
