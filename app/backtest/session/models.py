from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.backtest.config import (
    BacktestSessionConfig,
)


@dataclass(frozen=True)
class BacktestSessionResult:
    """
    Immutable backtest execution result.
    """

    config: BacktestSessionConfig
    processed_snapshots: int
    generated_trades: int
    started_at: datetime
    finished_at: datetime

    def __post_init__(self) -> None:

        if self.processed_snapshots < 0:
            raise ValueError(
                "processed_snapshots cannot be negative"
            )

        if self.generated_trades < 0:
            raise ValueError(
                "generated_trades cannot be negative"
            )

        if self.finished_at < self.started_at:
            raise ValueError(
                "finished_at cannot be before started_at"
            )
