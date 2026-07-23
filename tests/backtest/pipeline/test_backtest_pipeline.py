from app.backtest.pipeline import (
    BacktestPipelineOrchestrator,
    BacktestPipelineResult,
)
from app.backtest.report import (
    BacktestFinalReport,
)


def test_backtest_pipeline() -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-alpha",
        decision="PASS",
        rank=1,
        score=92.0,
        confidence=0.92,
        summary="Strong performance",
    )

    result = (
        BacktestPipelineOrchestrator()
        .run(
            report=report,
            risk_level="LOW",
        )
    )

    assert isinstance(
        result,
        BacktestPipelineResult,
    )

    assert (
        result.report.strategy_id
        == "strategy-alpha"
    )

    assert (
        result.summary.decision
        == "PASS"
    )

    assert (
        result.review.verdict
        == "APPROVE"
    )
