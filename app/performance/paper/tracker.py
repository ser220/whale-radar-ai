from __future__ import annotations

from typing import Iterable

from app.execution.paper_lifecycle import (
    PaperTradeResult,
)

from .models import PerformanceReport


class PaperPerformanceTracker:
    """
    Aggregates closed paper trade results.

    Statistics only.
    No strategy decisions.
    """

    def calculate(
        self,
        trades: Iterable[PaperTradeResult],
    ) -> PerformanceReport:

        trades = list(trades)

        for trade in trades:
            if not isinstance(
                trade,
                PaperTradeResult,
            ):
                raise TypeError(
                    "all items must be PaperTradeResult"
                )

        total = len(trades)

        winning = sum(
            1
            for trade in trades
            if trade.pnl > 0
        )

        losing = sum(
            1
            for trade in trades
            if trade.pnl < 0
        )

        total_pnl = sum(
            trade.pnl
            for trade in trades
        )

        average = (
            total_pnl / total
            if total
            else 0
        )

        win_rate = (
            winning / total
            if total
            else 0
        )

        return PerformanceReport(
            total_trades=total,
            winning_trades=winning,
            losing_trades=losing,
            total_pnl=round(
                total_pnl,
                6,
            ),
            average_pnl=round(
                average,
                6,
            ),
            win_rate=round(
                win_rate,
                4,
            ),
        )
