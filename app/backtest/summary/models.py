from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestAISummary:
    """
    AI interpretation layer for backtest results.
    """

    strategy_id: str
    decision: str
    headline: str
    explanation: str
    risk_level: str
    confidence: float

    def __post_init__(self) -> None:

        if not self.strategy_id:
            raise ValueError(
                "strategy_id cannot be empty"
            )

        if self.decision not in {
            "PASS",
            "REVIEW",
            "REJECT",
        }:
            raise ValueError(
                "invalid decision"
            )

        if self.risk_level not in {
            "LOW",
            "MEDIUM",
            "HIGH",
        }:
            raise ValueError(
                "invalid risk level"
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1"
            )
