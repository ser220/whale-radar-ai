from app.backtest.decision import (
    BacktestDecisionReport,
    DecisionReportCalculator,
)

from app.backtest.recommendation import (
    BacktestRecommendation,
)


def test_backtest_decision_report():

    recommendations = [
        BacktestRecommendation(
            strategy_id="strategy-alpha",
            decision="PASS",
            confidence=0.92,
            reason=(
                "Top ranked strategy "
                "with strong performance"
            ),
            final_score=92.0,
            rank=1,
        ),
        BacktestRecommendation(
            strategy_id="strategy-beta",
            decision="REVIEW",
            confidence=0.75,
            reason=(
                "Strategy requires "
                "additional review"
            ),
            final_score=75.0,
            rank=2,
        ),
    ]

    reports = (
        DecisionReportCalculator()
        .calculate(
            recommendations
        )
    )

    assert len(reports) == 2

    assert isinstance(
        reports[0],
        BacktestDecisionReport,
    )

    assert (
        reports[0].strategy_id
        == "strategy-alpha"
    )

    assert (
        reports[0].decision
        == "PASS"
    )

    assert (
        reports[0].rank
        == 1
    )

    assert (
        reports[1].decision
        == "REVIEW"
    )
