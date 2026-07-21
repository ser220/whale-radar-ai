from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskAssessment:
    """
    Immutable market risk assessment.

    Describes risk only.
    No trading decision allowed.
    """

    symbol: str
    risk_level: str
    risk_score: float
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        symbol = self.symbol.strip()
        risk_level = self.risk_level.strip()

        if not symbol:
            raise ValueError(
                "symbol is required"
            )

        if not risk_level:
            raise ValueError(
                "risk_level is required"
            )

        if (
            self.risk_score < 0
            or self.risk_score > 100
        ):
            raise ValueError(
                "risk_score must be between 0 and 100"
            )

        object.__setattr__(
            self,
            "symbol",
            symbol,
        )

        object.__setattr__(
            self,
            "risk_level",
            risk_level,
        )
