from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EquityPoint:
    """
    Single equity state point.
    """

    timestamp: datetime
    equity: float

    def __post_init__(self) -> None:

        if self.equity < 0:
            raise ValueError(
                "equity cannot be negative"
            )


@dataclass(frozen=True)
class BacktestEquityCurve:
    """
    Immutable equity curve result.
    """

    points: tuple[EquityPoint, ...]
    initial_balance: float
    final_equity: float
    cumulative_return: float
    peak_equity: float
    max_drawdown: float

    def __post_init__(self) -> None:

        if self.initial_balance <= 0:
            raise ValueError(
                "initial_balance must be positive"
            )

        if self.final_equity < 0:
            raise ValueError(
                "final_equity cannot be negative"
            )

        if self.max_drawdown < 0:
            raise ValueError(
                "max_drawdown cannot be negative"
            )

        object.__setattr__(
            self,
            "points",
            tuple(self.points),
        )
