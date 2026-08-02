"""Candidate reputation score contract."""

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
class CandidateReputationScore:
    """
    Long-term quality assessment of a candidate.
    """

    asset: str
    score: float
    stability_score: float
    promotion_quality: float
    risk_score: float

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
            "score",
            _validate_score(
                self.score,
                "score",
            ),
        )

        object.__setattr__(
            self,
            "stability_score",
            _validate_score(
                self.stability_score,
                "stability_score",
            ),
        )

        object.__setattr__(
            self,
            "promotion_quality",
            _validate_score(
                self.promotion_quality,
                "promotion_quality",
            ),
        )

        object.__setattr__(
            self,
            "risk_score",
            _validate_score(
                self.risk_score,
                "risk_score",
            ),
        )


__all__ = [
    "CandidateReputationScore",
]
