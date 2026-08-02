from app.intelligence.early_bird.candidate_ranking_record import (
    CandidateRankingRecord,
)


def test_candidate_ranking_record():

    record = CandidateRankingRecord(
        asset="HYPE",
        direction="REVERSAL",
        rank="S4",
        score=92.0,
        confidence=88.0,
        risk_score=30.0,
        priority=95.0,
    )

    assert record.asset == "HYPE"
    assert record.direction == "REVERSAL"
    assert record.rank == "S4"
    assert record.score == 92.0
    assert record.priority == 95.0



def test_invalid_direction():

    try:
        CandidateRankingRecord(
            asset="BTC",
            direction="UNKNOWN",
            rank="L1",
            score=50.0,
            confidence=50.0,
            risk_score=20.0,
            priority=40.0,
        )

    except ValueError as exc:
        assert "direction" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
