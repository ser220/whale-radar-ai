"""Candidate behaviour scoring contract."""

from dataclasses import dataclass


def _required_asset(
    value: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            "asset must be a string"
        )

    normalized = value.strip().upper()

    if not normalized:
        raise ValueError(
            "asset must not be empty"
        )

    return normalized


def _score(
    value: float,
    field_name: str,
) -> float:
    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(
            "{0} must be numeric".format(
                field_name
            )
        )

    normalized = float(value)

    if not 0.0 <= normalized <= 100.0:
        raise ValueError(
            "{0} must be between 0 and 100".format(
                field_name
            )
        )

    return normalized


@dataclass(frozen=True)
class CandidateBehaviorScore:
    """
    Normalized behaviour assessment of one candidate.
    """

    asset: str
    behavior_direction: str
    strength_score: float
    decay_score: float
    confidence: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "asset",
            _required_asset(
                self.asset
            ),
        )

        if not isinstance(
            self.behavior_direction,
            str,
        ):
            raise TypeError(
                "behavior_direction must be a string"
            )

        direction = (
            self.behavior_direction
            .strip()
            .lower()
        )

        allowed = {
            "strengthening",
            "stable",
            "weakening",
            "insufficient",
        }

        if direction not in allowed:
            raise ValueError(
                "invalid behavior_direction"
            )

        object.__setattr__(
            self,
            "behavior_direction",
            direction,
        )

        object.__setattr__(
            self,
            "strength_score",
            _score(
                self.strength_score,
                "strength_score",
            ),
        )

        object.__setattr__(
            self,
            "decay_score",
            _score(
                self.decay_score,
                "decay_score",
            ),
        )

        object.__setattr__(
            self,
            "confidence",
            _score(
                self.confidence,
                "confidence",
            ),
        )


__all__ = [
    "CandidateBehaviorScore",
]
