"""Perpetual direction decision contract."""

from dataclasses import dataclass


VALID_DIRECTIONS = {
    "LONG",
    "SHORT",
    "WAIT",
}


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


def _validate_confidence(
    value: float,
) -> float:

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(
            "confidence must be numeric"
        )

    confidence = float(value)

    if not 0.0 <= confidence <= 100.0:
        raise ValueError(
            "confidence must be between 0 and 100"
        )

    return confidence


@dataclass(frozen=True)
class PerpetualDirectionDecision:
    """
    Final directional assessment for perpetual trading.

    Possible outcomes:
    - LONG
    - SHORT
    - WAIT
    """

    asset: str
    direction: str
    confidence: float
    market_regime: str
    reason: str
    risk_flags: tuple[str, ...]

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
            "confidence",
            _validate_confidence(
                self.confidence
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
            self.market_regime,
            str,
        ):
            raise TypeError(
                "market_regime must be string"
            )

        if not isinstance(
            self.reason,
            str,
        ):
            raise TypeError(
                "reason must be string"
            )

        if not isinstance(
            self.risk_flags,
            tuple,
        ):
            raise TypeError(
                "risk_flags must be tuple"
            )


__all__ = [
    "PerpetualDirectionDecision",
]
