from app.backtest.ranking import (
    RankingCalculator,
)

from app.backtest.recommendation import (
    RecommendationCalculator,
)


def test_ranking_to_recommendation_flow():

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
            "overall_score": 75.0,
            "risk_adjusted_score": 70.0,
            "alpha_score": 65.0,
            "drawdown_penalty": 8.0,
            "final_score": 75.0,
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

    assert (
        recommendations[0].strategy_id
        == "strategy-alpha"
    )

    assert (
        recommendations[0].decision
        == "PASS"
    )

    assert (
        recommendations[1].decision
        == "REVIEW"
    )
