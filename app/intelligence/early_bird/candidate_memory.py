"""Candidate long-term memory contract."""

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


def _validate_count(
    value: int,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(
        value,
        int,
    ):
        raise TypeError(
            f"{field_name} must be an integer"
        )

    if value < 0:
        raise ValueError(
            f"{field_name} count must not be negative"
        )

    return value


@dataclass(frozen=True)
class CandidateMemory:
    """
    Persistent behavioural memory of a candidate.
    """

    asset: str
    observations_count: int
    promotion_count: int
    downgrade_count: int
    current_rank: CandidateRank
    highest_rank: CandidateRank

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
            "observations_count",
            _validate_count(
                self.observations_count,
                "observations_count",
            ),
        )

        object.__setattr__(
            self,
            "promotion_count",
            _validate_count(
                self.promotion_count,
                "promotion_count",
            ),
        )

        object.__setattr__(
            self,
            "downgrade_count",
            _validate_count(
                self.downgrade_count,
                "downgrade_count",
            ),
        )

        if not isinstance(
            self.current_rank,
            CandidateRank,
        ):
            raise TypeError(
                "current_rank must be CandidateRank"
            )

        if not isinstance(
            self.highest_rank,
            CandidateRank,
        ):
            raise TypeError(
                "highest_rank must be CandidateRank"
            )


__all__ = [
    "CandidateMemory",
]
