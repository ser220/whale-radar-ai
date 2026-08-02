"""Candidate selection result contract."""

from dataclasses import dataclass

from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)


def _validate_asset(
    value: str,
) -> str:

    if not isinstance(value, str):
        raise TypeError(
            "asset must be a string"
        )

    asset = value.strip().upper()

    if not asset:
        raise ValueError(
            "asset must not be empty"
        )

    return asset


def _validate_score(
    value: float,
) -> float:

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(
            "score must be numeric"
        )

    score = float(value)

    if not 0.0 <= score <= 100.0:
        raise ValueError(
            "score must be between 0 and 100"
        )

    return score


@dataclass(frozen=True)
class CandidateSelectionResult:
    """
    Final candidate selection decision.
    """

    asset: str
    rank: CandidateRank
    reputation_score: float
    selection_reason: str

    def __post_init__(self) -> None:

        object.__setattr__(
            self,
            "asset",
            _validate_asset(
                self.asset
            ),
        )

        object.__setattr__(
            self,
            "reputation_score",
            _validate_score(
                self.reputation_score
            ),
        )

        if not isinstance(
            self.rank,
            CandidateRank,
        ):
            raise TypeError(
                "rank must be CandidateRank"
            )

        if not isinstance(
            self.selection_reason,
            str,
        ):
            raise TypeError(
                "selection_reason must be string"
            )


__all__ = [
    "CandidateSelectionResult",
]
