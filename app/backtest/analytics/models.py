from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestAnalyticsReport:
    """
    Immutable analytical metrics report.
    """

    total_return: float
    average_trade: float
    win_rate: float
    profit_factor: float
    total_trades: int

    def __post_init__(self) -> None:

        if self.total_trades < 0:
            raise ValueError(
                "total_trades cannot be negative"
            )

        if self.win_rate < 0 or self.win_rate > 1:
            raise ValueError(
                "win_rate must be between 0 and 1"
            )

        if self.profit_factor < 0:
            raise ValueError(
                "profit_factor cannot be negative"
            )
