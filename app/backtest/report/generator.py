from __future__ import annotations

from app.backtest.decision import (
    BacktestDecisionReport,
)

from .models import (
    BacktestFinalReport,
)

class ReportGenerator:
    """
    Generates final backtest reports from decision reports.
    """

    def generate(
        self,
        decision: BacktestDecisionReport,
    ) -> BacktestFinalReport:

        if not isinstance(
            decision,
            BacktestDecisionReport,
        ):
            raise TypeError(
                "decision must be BacktestDecisionReport"
            )

        return BacktestFinalReport(
            strategy_id=decision.strategy_id,
            decision=decision.decision,
            rank=decision.rank,
            score=decision.final_score,
            confidence=decision.confidence,
            summary=decision.summary,
        )
