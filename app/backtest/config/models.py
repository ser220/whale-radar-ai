from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BacktestSessionConfig:
    """
    Immutable backtest execution configuration.
    """

    symbol: str
    start_time: datetime
    end_time: datetime
    initial_balance: float

    def __post_init__(self) -> None:

        symbol = self.symbol.strip()

        if not symbol:
            raise ValueError(
                "symbol is required"
            )

        if self.end_time < self.start_time:
            raise ValueError(
                "end_time cannot be before start_time"
            )

        if self.initial_balance <= 0:
            raise ValueError(
                "initial_balance must be positive"
            )

        object.__setattr__(
            self,
            "symbol",
            symbol,
        )
