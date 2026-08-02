"""Candidate ranking record contract."""

from dataclasses import dataclass


VALID_DIRECTIONS = {
    "LONG",
    "SHORT",
    "REVERSAL",
}


def _validate_score(
    value: float,
    name: str,
) -> float:

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(
            f"{name} must be numeric"
        )

    score = float(value)

    if not 0.0 <= score <= 100.0:
        raise ValueError(
            f"{name} must be between 0 and 100"
        )

    return score


def _validate_asset(
    value: str,
) -> str:

    if not isinstance(value, str):
        raise TypeError(
            "asset must be string"
        )

    asset = value.strip().upper()

    if not asset:
        raise ValueError(
            "asset must not be empty"
        )

    return asset


@dataclass(frozen=True)
class CandidateRankingRecord:
    """
    Ranking record for perpetual candidate selection.

    Supports:

    LONG leaderboard
    SHORT leaderboard
    REVERSAL leaderboard
    """

    asset: str
    direction: str
    rank: str
    score: float
    confidence: float
    risk_score: float
    priority: float

    def __post_init__(self) -> None:

        object.__setattr__(
            self,
            "asset",
            _validate_asset(
                self.asset
            ),
        )

        direction = self.direction.upper()

        if direction not in VALID_DIRECTIONS:
            raise ValueError(
                "invalid direction"
            )

        object.__setattr__(
            self,
            "direction",
            direction,
        )

        if not isinstance(
            self.rank,
            str,
        ):
            raise TypeError(
                "rank must be string"
            )

        for field_name in (
            "score",
            "confidence",
            "risk_score",
            "priority",
        ):
            object.__setattr__(
                self,
                field_name,
                _validate_score(
                    getattr(
                        self,
                        field_name,
                    ),
                    field_name,
                ),
            )


__all__ = [
    "CandidateRankingRecord",
]
