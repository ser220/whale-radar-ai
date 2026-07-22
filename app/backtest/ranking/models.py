from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestStrategyRanking:
    """
    Ranking result for a backtested strategy.
    """

    strategy_id: str
    overall_score: float
    risk_adjusted_score: float
    alpha_score: float
    drawdown_penalty: float
    final_score: float
    rank: int

    def __post_init__(self) -> None:

        if not self.strategy_id:
            raise ValueError(
                "strategy_id cannot be empty"
            )

        if self.rank <= 0:
            raise ValueError(
                "rank must be positive"
            )

        if self.final_score < 0:
            raise ValueError(
                "final_score cannot be negative"
            )
