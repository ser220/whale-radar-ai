from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PerformanceReport:
    """
    Immutable paper trading performance report.

    Contains statistics only.
    No execution logic.
    """

    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    average_pnl: float
    win_rate: float

    def __post_init__(self) -> None:
        if self.total_trades < 0:
            raise ValueError(
                "total_trades cannot be negative"
            )

        if self.winning_trades < 0:
            raise ValueError(
                "winning_trades cannot be negative"
            )

        if self.losing_trades < 0:
            raise ValueError(
                "losing_trades cannot be negative"
            )

        if (
            self.winning_trades
            +
            self.losing_trades
            >
            self.total_trades
        ):
            raise ValueError(
                "trade counts exceed total trades"
            )

        if (
            self.win_rate < 0
            or self.win_rate > 1
        ):
            raise ValueError(
                "win_rate must be between 0 and 1"
            )
