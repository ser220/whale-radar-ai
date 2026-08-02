from datetime import datetime, timezone

from app.intelligence.early_bird.rank_cascade_engine import (
    RankCascadeEngine,
)

from app.intelligence.early_bird.candidate_ranking_record import (
    CandidateRankingRecord,
)

from app.intelligence.early_bird.candidate_leaderboard import (
    CandidateLeaderboard,
)

from app.intelligence.early_bird.perpetual_opportunity_selector import (
    PerpetualOpportunitySelector,
)


def test_cascade_pool_flows_into_perpetual_selector():

    cascade = RankCascadeEngine().evaluate(
        asset="HYPE",
        long_score=85,
        short_score=20,
    )

    record = CandidateRankingRecord(
        asset=cascade.asset,
        direction="LONG",
        rank=cascade.long_rank,
        score=cascade.long_score,
        confidence=cascade.long_score,
        risk_score=20,
        priority=cascade.long_score,
    )

    leaderboard = CandidateLeaderboard(
        long_candidates=(record,),
        short_candidates=(),
        reversal_candidates=(),
        timestamp=datetime.now(timezone.utc),
    )

    opportunity = PerpetualOpportunitySelector().select(
        leaderboard
    )

    assert opportunity.asset == "HYPE"
    assert opportunity.direction == "LONG"
    assert opportunity.rank == "L4"
