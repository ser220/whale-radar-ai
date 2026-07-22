from app.backtest.ranking import (
    RankingCalculator,
)

from app.backtest.evaluation import (
    BacktestEvaluationReport,
)


def test_evaluation_to_ranking_flow():

    strategies = [
        {
            "strategy_id": "strategy-alpha",
            "overall_score": 92.0,
            "risk_adjusted_score": 90.0,
            "alpha_score": 85.0,
            "drawdown_penalty": 3.0,
            "final_score": 92.0,
        },
        {
            "strategy_id": "strategy-beta",
            "overall_score": 78.0,
            "risk_adjusted_score": 80.0,
            "alpha_score": 70.0,
            "drawdown_penalty": 8.0,
            "final_score": 78.0,
        },
    ]

    ranking = (
        RankingCalculator()
        .calculate(
            strategies
        )
    )

    assert len(ranking) == 2

    assert (
        ranking[0].strategy_id
        == "strategy-alpha"
    )

    assert (
        ranking[0].rank
        == 1
    )

    assert (
        ranking[1].strategy_id
        == "strategy-beta"
    )

    assert (
        ranking[1].rank
        == 2
    )

    assert (
        ranking[0].final_score
        >
        ranking[1].final_score
    )
