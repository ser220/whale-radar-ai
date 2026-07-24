from typing import get_type_hints

from app.backtest.report import (
    BacktestFinalReport,
    ReportGenerator,
)

from app.backtest.decision import (
    BacktestDecisionReport,
)


def test_report_generator_return_type_hint_resolves() -> None:
    type_hints = get_type_hints(
        ReportGenerator.generate
    )

    assert type_hints["return"] is (
        BacktestFinalReport
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
