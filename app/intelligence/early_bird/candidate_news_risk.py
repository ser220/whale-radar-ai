"""Candidate news risk contract."""

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
class CandidateNewsRisk:
    """
    External event uncertainty assessment.

    News does not directly decide LONG/SHORT.
    It modifies confidence and risk.
    """

    asset: str
    news_pressure_score: float
    event_type: str
    directional_bias: str
    uncertainty_score: float

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
            "news_pressure_score",
            _validate_score(
                self.news_pressure_score,
                "news_pressure_score",
            ),
        )

        object.__setattr__(
            self,
            "uncertainty_score",
            _validate_score(
                self.uncertainty_score,
                "uncertainty_score",
            ),
        )

        if not isinstance(
            self.event_type,
            str,
        ):
            raise TypeError(
                "event_type must be string"
            )

        if not isinstance(
            self.directional_bias,
            str,
        ):
            raise TypeError(
                "directional_bias must be string"
            )


__all__ = [
    "CandidateNewsRisk",
]
