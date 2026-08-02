"""Perpetual opportunity contract."""

from dataclasses import dataclass


VALID_DIRECTIONS = {
    "LONG",
    "SHORT",
}

VALID_SETUP_TYPES = {
    "CONTINUATION",
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
class PerpetualOpportunity:
    """
    Final candidate opportunity for perpetual analysis.

    Represents:

    LONG continuation

    SHORT continuation

    LONG -> SHORT reversal
    """

    asset: str
    direction: str
    setup_type: str
    rank: str
    score: float
    priority: float
    confidence: float
    reason: str

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

        setup = self.setup_type.upper()

        if setup not in VALID_SETUP_TYPES:
            raise ValueError(
                "invalid setup_type"
            )

        object.__setattr__(
            self,
            "setup_type",
            setup,
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
            "priority",
            "confidence",
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

        if not isinstance(
            self.reason,
            str,
        ):
            raise TypeError(
                "reason must be string"
            )


__all__ = [
    "PerpetualOpportunity",
]
