"""Ranking feedback signal contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RankingFeedbackSignal:
    """
    Immutable feedback signal for candidate ranking adjustment.

    Represents historical performance influence,
    not a direct ranking decision.
    """

    pattern: str
    direction: str
    confidence_adjustment: float
    reason: str

    def __post_init__(self) -> None:

        for field_name in (
            "pattern",
            "direction",
            "reason",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"{field_name} must be string"
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} must not be empty"
                )

        object.__setattr__(
            self,
            "pattern",
            self.pattern.upper(),
        )

        object.__setattr__(
            self,
            "direction",
            self.direction.upper(),
        )

        if not isinstance(
            self.confidence_adjustment,
            (int, float),
        ):
            raise TypeError(
                "adjustment must be numeric"
            )

        if not -100.0 <= self.confidence_adjustment <= 100.0:
            raise ValueError(
                "adjustment must be between -100 and 100"
            )


__all__ = [
    "RankingFeedbackSignal",
]
