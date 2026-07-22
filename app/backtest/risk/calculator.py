from __future__ import annotations

from app.backtest.equity import (
    BacktestEquityCurve,
)

from .models import (
    BacktestRiskReport,
)


class RiskMetricsCalculator:
    """
    Calculates risk metrics from equity curve.

    No strategy logic.
    No execution logic.
    """

    def calculate(
        self,
        curve: BacktestEquityCurve,
    ) -> BacktestRiskReport:

        if not isinstance(
            curve,
            BacktestEquityCurve,
        ):
            raise TypeError(
                "curve must be BacktestEquityCurve"
            )

        max_drawdown = curve.max_drawdown

        if curve.peak_equity > 0:
            max_drawdown_percent = (
                max_drawdown
                /
                curve.peak_equity
            )
        else:
            max_drawdown_percent = 0.0

        total_return = (
            curve.final_equity
            -
            curve.initial_balance
        )

        if max_drawdown > 0:
            recovery_factor = (
                max(
                    total_return,
                    0
                )
                /
                max_drawdown
            )
        else:
            recovery_factor = 0.0

        risk_score = max(
            0.0,
            min(
                1.0,
                1.0
                -
                max_drawdown_percent,
            ),
        )

        return BacktestRiskReport(
            max_drawdown=max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            recovery_factor=recovery_factor,
            risk_score=risk_score,
        )
