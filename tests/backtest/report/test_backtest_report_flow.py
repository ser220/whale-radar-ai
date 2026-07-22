from app.backtest.recommendation import (
    BacktestRecommendation,
)

from app.backtest.decision import (
    DecisionReportCalculator,
)

from app.backtest.report import (
    ReportGenerator,
)


def test_full_backtest_report_flow():

    recommendation = BacktestRecommendation(
        strategy_id="strategy-alpha",
        decision="PASS",
        rank=1,
        final_score=92.0,
        confidence=0.92,
        reason=(
            "Top ranked strategy "
            "with strong risk profile"
        ),
    )

    decision = (
        DecisionReportCalculator()
        .calculate(
            [
                recommendation
            ]
        )[0]
    )

    report = (
        ReportGenerator()
        .generate(
            decision
        )
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
