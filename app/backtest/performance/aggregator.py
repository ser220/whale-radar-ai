from __future__ import annotations

from typing import Iterable

from app.execution.paper_lifecycle import (
    PaperTradeResult,
)

from .models import (
    BacktestPerformanceReport,
)


class BacktestPerformanceAggregator:
    """
    Aggregates paper trade results
    into a backtest performance report.
    """

    def aggregate(
        self,
        trades: Iterable[PaperTradeResult],
    ) -> BacktestPerformanceReport:
        trades = list(
            trades
        )

        for trade in trades:
            if not isinstance(
                trade,
                PaperTradeResult,
            ):
                raise TypeError(
                    "all items must be PaperTradeResult"
                )

        total_trades = len(
            trades
        )

        winning_trades = sum(
            1
            for trade in trades
            if trade.pnl > 0
        )

        losing_trades = sum(
            1
            for trade in trades
            if trade.pnl < 0
        )

        total_pnl = sum(
            trade.pnl
            for trade in trades
        )

        average_pnl = (
            total_pnl / total_trades
            if total_trades
            else 0.0
        )

        win_rate = (
            winning_trades / total_trades
            if total_trades
            else 0.0
        )

        gross_profit = sum(
            trade.pnl
            for trade in trades
            if trade.pnl > 0
        )

        gross_loss = abs(
            sum(
                trade.pnl
                for trade in trades
                if trade.pnl < 0
            )
        )

        if gross_loss > 0:
            profit_factor = (
                gross_profit / gross_loss
            )
        elif gross_profit > 0:
            profit_factor = float(
                "inf"
            )
        else:
            profit_factor = 0.0

        return BacktestPerformanceReport(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_pnl=round(
                total_pnl,
                6,
            ),
            average_pnl=round(
                average_pnl,
                6,
            ),
            win_rate=round(
                win_rate,
                4,
            ),
            profit_factor=round(
                profit_factor,
                6,
            ),
        )
