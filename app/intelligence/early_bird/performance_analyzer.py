"""Performance analyzer."""

from dataclasses import dataclass

from app.intelligence.early_bird.execution_performance_memory import (
    ExecutionPerformanceMemory,
)


@dataclass(frozen=True)
class PerformanceMetrics:
    """
    Aggregated execution performance metrics.
    """

    total_trades: int
    successful_trades: int
    win_rate: float
    average_profit_loss: float


class PerformanceAnalyzer:
    """
    Converts execution history into performance metrics.
    """

    def analyze(
        self,
        memory: ExecutionPerformanceMemory,
    ) -> PerformanceMetrics:

        records = memory.get_all()

        total = len(records)

        if total == 0:
            return PerformanceMetrics(
                total_trades=0,
                successful_trades=0,
                win_rate=0.0,
                average_profit_loss=0.0,
            )

        successful = sum(
            1
            for record in records
            if record.success
        )

        total_profit = sum(
            record.profit_loss
            for record in records
        )

        return PerformanceMetrics(
            total_trades=total,
            successful_trades=successful,
            win_rate=(
                successful / total
            ) * 100.0,
            average_profit_loss=(
                total_profit / total
            ),
        )


__all__ = [
    "PerformanceAnalyzer",
    "PerformanceMetrics",
]
