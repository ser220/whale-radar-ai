from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestRiskReport:
    """
    Immutable risk analysis result.
    """

    max_drawdown: float
    max_drawdown_percent: float
    recovery_factor: float
    risk_score: float

    def __post_init__(self) -> None:

        if self.max_drawdown < 0:
            raise ValueError(
                "max_drawdown cannot be negative"
            )

        if self.max_drawdown_percent < 0:
            raise ValueError(
                "max_drawdown_percent cannot be negative"
            )

        if self.recovery_factor < 0:
            raise ValueError(
                "recovery_factor cannot be negative"
            )

        if (
            self.risk_score < 0
            or self.risk_score > 1
        ):
            raise ValueError(
                "risk_score must be between 0 and 1"
            )
