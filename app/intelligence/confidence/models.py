from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionConfidence:
    """
    Immutable aggregated decision confidence.

    Represents confidence only.
    No trading decision allowed.
    """

    symbol: str
    confidence: float
    level: str

    def __post_init__(self) -> None:
        symbol = self.symbol.strip()
        level = self.level.strip()

        if not symbol:
            raise ValueError(
                "symbol is required"
            )

        if (
            self.confidence < 0
            or self.confidence > 1
        ):
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        if not level:
            raise ValueError(
                "level is required"
            )

        object.__setattr__(
            self,
            "symbol",
            symbol,
        )

        object.__setattr__(
            self,
            "level",
            level,
        )
