from __future__ import annotations

from typing import Iterable

from app.execution.paper_lifecycle import (
    PaperTradeResult,
)

from .models import (
    BacktestEquityCurve,
    EquityPoint,
)


class EquityCurveCalculator:
    """
    Calculates equity curve from closed paper trades.

    No execution logic.
    No strategy logic.
    """

    def calculate(
        self,
        trades: Iterable[PaperTradeResult],
        initial_balance: float,
    ) -> BacktestEquityCurve:

        if initial_balance <= 0:
            raise ValueError(
                "initial_balance must be positive"
            )

        trades = list(trades)

        for trade in trades:
            if not isinstance(
                trade,
                PaperTradeResult,
            ):
                raise TypeError(
                    "all items must be PaperTradeResult"
                )

        equity = initial_balance
        peak = initial_balance
        max_drawdown = 0.0

        points = []

        for trade in trades:
            equity += trade.pnl

            if equity > peak:
                peak = equity

            drawdown = (
                peak - equity
            )

            if drawdown > max_drawdown:
                max_drawdown = drawdown

            points.append(
                EquityPoint(
                    timestamp=trade.closed_at,
                    equity=equity,
                )
            )

        cumulative_return = (
            (equity - initial_balance)
            /
            initial_balance
        )

        return BacktestEquityCurve(
            points=tuple(points),
            initial_balance=initial_balance,
            final_equity=equity,
            cumulative_return=cumulative_return,
            peak_equity=peak,
            max_drawdown=max_drawdown,
        )
