from app.backtest.pipeline import (
    BacktestPipelineOrchestrator,
)
from app.backtest.report import (
    BacktestFinalReport,
)


def test_backtest_pipeline_full_flow() -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-beta",
        decision="PASS",
        rank=2,
        score=88.0,
        confidence=0.88,
        summary="Consistent backtest performance",
    )

    result = BacktestPipelineOrchestrator().run(
        report=report,
        risk_level="MEDIUM",
    )

    assert result.report is report

    assert (
        result.report.strategy_id
        == result.summary.strategy_id
        == result.review.strategy_id
    )

    assert (
        result.report.decision
        == result.summary.decision
    )

    assert (
        result.summary.confidence
        == result.review.confidence
    )

    assert result.summary.risk_level == "MEDIUM"

    assert result.review.verdict == "APPROVE"
