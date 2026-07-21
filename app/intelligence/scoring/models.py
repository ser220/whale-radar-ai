from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntelligenceScore:
    """
    Immutable intelligence quality score.

    Represents market quality only.
    No trading decision allowed.
    """

    symbol: str
    score: float
    confidence: float

    def __post_init__(self) -> None:
        symbol = self.symbol.strip()

        if not symbol:
            raise ValueError(
                "symbol is required"
            )

        if self.score < 0 or self.score > 100:
            raise ValueError(
                "score must be between 0 and 100"
            )

        if (
            self.confidence < 0
            or self.confidence > 1
        ):
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        object.__setattr__(
            self,
            "symbol",
            symbol,
        )
