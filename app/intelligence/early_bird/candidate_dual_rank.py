"""Dual directional rank contract."""

from dataclasses import dataclass


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


@dataclass(frozen=True)
class CandidateDualRank:
    """
    Simultaneous LONG and SHORT ranking.

    A candidate can evolve from:
    LONG dominant
    ->
    REVERSAL
    ->
    SHORT dominant
    """

    asset: str
    long_rank: str
    short_rank: str
    long_score: float
    short_score: float
    transition_state: str

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
            "long_score",
            _validate_score(
                self.long_score,
                "long_score",
            ),
        )

        object.__setattr__(
            self,
            "short_score",
            _validate_score(
                self.short_score,
                "short_score",
            ),
        )

        if not isinstance(
            self.long_rank,
            str,
        ):
            raise TypeError(
                "long_rank must be string"
            )

        if not isinstance(
            self.short_rank,
            str,
        ):
            raise TypeError(
                "short_rank must be string"
            )

        if not isinstance(
            self.transition_state,
            str,
        ):
            raise TypeError(
                "transition_state must be string"
            )


__all__ = [
    "CandidateDualRank",
]
