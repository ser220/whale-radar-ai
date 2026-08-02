"""Perpetual execution readiness contract."""

from dataclasses import dataclass


VALID_DIRECTIONS = {
    "LONG",
    "SHORT",
}

VALID_STATUSES = {
    "WAIT",
    "PREPARE",
    "READY",
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
class PerpetualExecutionReadiness:
    """
    Execution gate before perpetual trading.

    Separates:

    opportunity quality

    from

    execution permission
    """

    asset: str
    direction: str
    status: str
    confidence: float
    risk_score: float
    news_risk: float
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

        status = self.status.upper()

        if status not in VALID_STATUSES:
            raise ValueError(
                "invalid status"
            )

        object.__setattr__(
            self,
            "status",
            status,
        )

        for field_name in (
            "confidence",
            "risk_score",
            "news_risk",
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
    "PerpetualExecutionReadiness",
]
