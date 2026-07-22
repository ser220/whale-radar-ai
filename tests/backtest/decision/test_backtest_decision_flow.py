from app.backtest.ranking import (
    RankingCalculator,
)

from app.backtest.recommendation import (
    RecommendationCalculator,
)

from app.backtest.decision import (
    DecisionReportCalculator,
)


def test_full_backtest_decision_flow():

    strategies = [
        {
            "strategy_id": "strategy-alpha",
            "overall_score": 92.0,
            "risk_adjusted_score": 90.0,
            "alpha_score": 88.0,
            "drawdown_penalty": 3.0,
            "final_score": 92.0,
        },
        {
            "strategy_id": "strategy-beta",
            "overall_score": 65.0,
            "risk_adjusted_score": 63.0,
            "alpha_score": 60.0,
            "drawdown_penalty": 10.0,
            "final_score": 65.0,
        },
    ]

    ranked = (
        RankingCalculator()
        .calculate(
            strategies
        )
    )

    ranking_payload = [
        {
            "strategy_id": item.strategy_id,
            "rank": item.rank,
            "final_score": item.final_score,
        }
        for item in ranked
    ]

    recommendations = (
        RecommendationCalculator()
        .calculate(
            ranking_payload
        )
    )

    reports = (
        DecisionReportCalculator()
        .calculate(
            recommendations
        )
    )

    assert len(reports) == 2

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
