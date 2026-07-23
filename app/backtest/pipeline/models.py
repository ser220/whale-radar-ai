from __future__ import annotations

from dataclasses import dataclass

from app.backtest.report import (
    BacktestFinalReport,
)
from app.backtest.review import (
    BacktestAIReview,
)
from app.backtest.summary import (
    BacktestAISummary,
)


@dataclass(frozen=True)
class BacktestPipelineResult:
    """
    Unified result of the completed backtest pipeline.
    """

    report: BacktestFinalReport
    summary: BacktestAISummary
    review: BacktestAIReview

    def __post_init__(self) -> None:
        strategy_ids = {
            self.report.strategy_id,
            self.summary.strategy_id,
            self.review.strategy_id,
        }

        if len(strategy_ids) != 1:
            raise ValueError(
                "pipeline strategy_id values must match"
            )

        if self.report.decision != self.summary.decision:
            raise ValueError(
                "report and summary decisions must match"
            )

        if self.summary.confidence != self.review.confidence:
            raise ValueError(
                "summary and review confidence must match"
            )
