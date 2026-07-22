from __future__ import annotations

from dataclasses import dataclass

from app.backtest.session import (
    BacktestSessionResult,
)

from app.backtest.performance import (
    BacktestPerformanceReport,
)


@dataclass(frozen=True)
class BacktestReport:
    """
    Immutable unified backtest report.
    """

    session: BacktestSessionResult
    performance: BacktestPerformanceReport

    def __post_init__(self) -> None:

        if not isinstance(
            self.session,
            BacktestSessionResult,
        ):
            raise TypeError(
                "session must be BacktestSessionResult"
            )

        if not isinstance(
            self.performance,
            BacktestPerformanceReport,
        ):
            raise TypeError(
                "performance must be BacktestPerformanceReport"
            )
