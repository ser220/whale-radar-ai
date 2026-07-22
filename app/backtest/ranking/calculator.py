from __future__ import annotations

from typing import Iterable

from .models import (
    BacktestStrategyRanking,
)


class RankingCalculator:
    """
    Calculates strategy ranking based on evaluation scores.
    """

    def calculate(
        self,
        strategies: Iterable[dict],
    ) -> list[BacktestStrategyRanking]:

        ranked = []

        sorted_strategies = sorted(
            strategies,
            key=lambda item: item["final_score"],
            reverse=True,
        )

        for index, strategy in enumerate(
            sorted_strategies,
            start=1,
        ):
            ranked.append(
                BacktestStrategyRanking(
                    strategy_id=strategy["strategy_id"],
                    overall_score=strategy["overall_score"],
                    risk_adjusted_score=strategy["risk_adjusted_score"],
                    alpha_score=strategy["alpha_score"],
                    drawdown_penalty=strategy["drawdown_penalty"],
                    final_score=strategy["final_score"],
                    rank=index,
                )
            )

        return ranked
