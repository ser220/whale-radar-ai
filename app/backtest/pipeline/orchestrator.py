from typing import Optional

from app.backtest.pipeline.models import (
    BacktestPipelineResult,
)
from app.backtest.report import (
    BacktestFinalReport,
)
from app.backtest.review import (
    AIReviewGenerator,
)
from app.backtest.summary import (
    AISummaryGenerator,
)


class BacktestPipelineOrchestrator:
    """
    Orchestrates the final backtest reporting pipeline.
    """

    def __init__(
        self,
        summary_generator: Optional[AISummaryGenerator] = None,
        review_generator: Optional[AIReviewGenerator] = None,
    ) -> None:
        self._summary_generator = (
            summary_generator
            or AISummaryGenerator()
        )
        self._review_generator = (
            review_generator
            or AIReviewGenerator()
        )

    def run(
        self,
        report: BacktestFinalReport,
        risk_level: str,
    ) -> BacktestPipelineResult:
        summary = self._summary_generator.generate(
            strategy_id=report.strategy_id,
            decision=report.decision,
            score=report.score,
            risk_level=risk_level,
            confidence=report.confidence,
        )

        review = self._review_generator.generate(
            strategy_id=summary.strategy_id,
            decision=summary.decision,
            confidence=summary.confidence,
        )

        return BacktestPipelineResult(
            report=report,
            summary=summary,
            review=review,
        )
