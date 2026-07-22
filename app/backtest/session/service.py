from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from app.backtest.config import (
    BacktestSessionConfig,
)

from app.simulation import (
    SimulationRunner,
    SimulationSnapshot,
)

from .models import (
    BacktestSessionResult,
)


class BacktestSessionService:
    """
    Coordinates backtest execution boundary.
    """

    def __init__(
        self,
        runner: SimulationRunner | None = None,
    ) -> None:

        self._runner = (
            runner
            if runner is not None
            else SimulationRunner()
        )

    def run(
        self,
        config: BacktestSessionConfig,
        snapshots: Iterable[SimulationSnapshot],
    ) -> BacktestSessionResult:

        started_at = datetime.now(
            timezone.utc
        )

        result = self._runner.run(
            snapshots
        )

        finished_at = datetime.now(
            timezone.utc
        )

        return BacktestSessionResult(
            config=config,
            processed_snapshots=(
                result.processed_snapshots
            ),
            generated_trades=(
                result.generated_trades
            ),
            started_at=started_at,
            finished_at=finished_at,
        )
