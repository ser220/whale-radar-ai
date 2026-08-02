from app.intelligence.early_bird.candidate_selection_result import (
    CandidateSelectionResult,
)
from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)


def test_candidate_selection_result_contract():

    result = CandidateSelectionResult(
        asset="HYPE",
        rank=CandidateRank.PRIME,
        reputation_score=87.0,
        selection_reason=(
            "high reputation candidate"
        ),
    )

    assert result.asset == "HYPE"
    assert result.rank == CandidateRank.PRIME
    assert result.reputation_score == 87.0
    assert (
        result.selection_reason
        ==
        "high reputation candidate"
    )


def test_selection_result_rejects_invalid_score():

    try:
        CandidateSelectionResult(
            asset="BTC",
            rank=CandidateRank.WATCHLIST,
            reputation_score=120.0,
            selection_reason="invalid",
        )
    except ValueError as exc:
        assert "score" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )
