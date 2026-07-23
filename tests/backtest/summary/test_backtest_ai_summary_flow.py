from app.backtest.summary import (
    AISummaryGenerator,
)

from app.backtest.report import (
    BacktestFinalReport,
)


def test_backtest_ai_summary_flow():

    report = BacktestFinalReport(
        strategy_id="strategy-alpha",
        decision="PASS",
        rank=1,
        score=92.0,
        confidence=0.92,
        summary="Strong performance with low risk",
    )

    summary = (
        AISummaryGenerator()
        .generate(
            strategy_id=report.strategy_id,
            decision=report.decision,
            score=report.score,
            risk_level="LOW",
            confidence=report.confidence,
        )
    )

    assert (
        summary.strategy_id
        == "strategy-alpha"
    )

    assert (
        summary.decision
        == "PASS"
    )

    assert (
        summary.risk_level
        == "LOW"
    )

    assert (
        summary.confidence
        == 0.92
    )
