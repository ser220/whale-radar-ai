from app.backtest.report import (
    BacktestFinalReport,
    ReportGenerator,
)

from app.backtest.decision import (
    BacktestDecisionReport,
)


def test_backtest_report():

    decision = BacktestDecisionReport(
        strategy_id="strategy-alpha",
        decision="PASS",
        rank=1,
        final_score=92.0,
        confidence=0.92,
        summary=(
            "Strong performance "
            "with controlled risk"
        ),
    )

    report = (
        ReportGenerator()
        .generate(
            decision
        )
    )

    assert isinstance(
        report,
        BacktestFinalReport,
    )

    assert (
        report.strategy_id
        == "strategy-alpha"
    )

    assert (
        report.decision
        == "PASS"
    )

    assert (
        report.rank
        == 1
    )

    assert (
        report.score
        == 92.0
    )

    assert (
        report.confidence
        == 0.92
    )
