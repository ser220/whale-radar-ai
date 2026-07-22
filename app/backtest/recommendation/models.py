from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestRecommendation:
    """
    Final recommendation result for a backtested strategy.
    """

    strategy_id: str
    decision: str
    confidence: float
    reason: str
    final_score: float
    rank: int

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
                "invalid recommendation decision"
            )

        if self.confidence < 0 or self.confidence > 1:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        if self.rank <= 0:
            raise ValueError(
                "rank must be positive"
            )

        if self.final_score < 0:
            raise ValueError(
                "final_score cannot be negative"
            )
