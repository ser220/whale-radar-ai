from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestBenchmarkReport:
    """
    Immutable benchmark comparison result.
    """

    strategy_return: float
    benchmark_return: float
    alpha: float
    outperformance: float
    benchmark_win: bool

    def __post_init__(self) -> None:

        if not isinstance(
            self.benchmark_win,
            bool,
        ):
            raise ValueError(
                "benchmark_win must be bool"
            )
