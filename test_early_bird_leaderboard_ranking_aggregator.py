from app.intelligence.early_bird.candidate_ranking_record import (
    CandidateRankingRecord,
)

from app.intelligence.early_bird.leaderboard_ranking_aggregator import (
    LeaderboardRankingAggregator,
)


def test_aggregates_directional_leaderboards():

    records = (
        CandidateRankingRecord(
            asset="SOL",
            direction="LONG",
            rank="L4",
            score=90.0,
            confidence=88.0,
            risk_score=20.0,
            priority=92.0,
        ),
        CandidateRankingRecord(
            asset="HYPE",
            direction="REVERSAL",
            rank="S4",
            score=86.0,
            confidence=92.0,
            risk_score=25.0,
            priority=99.0,
        ),
        CandidateRankingRecord(
            asset="AVAX",
            direction="SHORT",
            rank="S4",
            score=91.0,
            confidence=85.0,
            risk_score=30.0,
            priority=90.0,
        ),
    )

    result = LeaderboardRankingAggregator().aggregate(
        records
    )

    assert result.long_candidates[0].asset == "SOL"
    assert result.short_candidates[0].asset == "AVAX"
    assert result.reversal_candidates[0].asset == "HYPE"



def test_top_limit_is_applied():

    records = tuple(
        CandidateRankingRecord(
            asset=f"COIN{i}",
            direction="LONG",
            rank="L4",
            score=float(i),
            confidence=80.0,
            risk_score=20.0,
            priority=float(i),
        )
        for i in range(20)
    )

    result = LeaderboardRankingAggregator(
        max_candidates=5
    ).aggregate(
        records
    )

    assert len(
        result.long_candidates
    ) == 5
