from app.backtest.recommendation import (
    BacktestRecommendation,
    RecommendationCalculator,
)


def test_backtest_recommendation():

    strategies = [
        {
            "strategy_id": "strategy-alpha",
            "rank": 1,
            "final_score": 90.0,
        },
        {
            "strategy_id": "strategy-beta",
            "rank": 2,
            "final_score": 70.0,
        },
        {
            "strategy_id": "strategy-gamma",
            "rank": 3,
            "final_score": 40.0,
        },
    ]

    recommendations = (
        RecommendationCalculator()
        .calculate(
            strategies
        )
    )

    assert len(recommendations) == 3

    assert isinstance(
        recommendations[0],
        BacktestRecommendation,
    )

    assert (
        recommendations[0].decision
        == "PASS"
    )

    assert (
        recommendations[1].decision
        == "REVIEW"
    )

    assert (
        recommendations[2].decision
        == "REJECT"
    )
