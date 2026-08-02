"""Candidate directional score contract."""

from dataclasses import dataclass


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
    field_name: str,
) -> float:

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(
            f"{field_name} must be numeric"
        )

    score = float(value)

    if not 0.0 <= score <= 100.0:
        raise ValueError(
            f"{field_name} must be between 0 and 100"
        )

    return score


@dataclass(frozen=True)
class CandidateDirectionalScore:
    """
    Two-sided perpetual market assessment.

    A candidate can simultaneously have:
    - long opportunity
    - short opportunity
    """

    asset: str
    long_score: float
    short_score: float
    long_rank: str
    short_rank: str
    market_regime: str
    confidence: float

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

        object.__setattr__(
            self,
            "confidence",
            _validate_score(
                self.confidence,
                "confidence",
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
            self.market_regime,
            str,
        ):
            raise TypeError(
                "market_regime must be string"
            )


__all__ = [
    "CandidateDirectionalScore",
]
