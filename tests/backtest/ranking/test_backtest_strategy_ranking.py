from app.backtest.ranking import (
    RankingCalculator,
    BacktestStrategyRanking,
)


def test_strategy_ranking():

    strategies = [
        {
            "strategy_id": "strategy-a",
            "overall_score": 90.0,
            "risk_adjusted_score": 85.0,
            "alpha_score": 80.0,
            "drawdown_penalty": 5.0,
            "final_score": 90.0,
        },
        {
            "strategy_id": "strategy-b",
            "overall_score": 70.0,
            "risk_adjusted_score": 65.0,
            "alpha_score": 60.0,
            "drawdown_penalty": 10.0,
            "final_score": 70.0,
        },
    ]

    ranking = (
        RankingCalculator()
        .calculate(
            strategies
        )
    )

    assert len(ranking) == 2

    assert isinstance(
        ranking[0],
        BacktestStrategyRanking,
    )

    assert (
        ranking[0].strategy_id
        == "strategy-a"
    )

    assert (
        ranking[0].rank
        == 1
    )

    assert (
        ranking[1].strategy_id
        == "strategy-b"
    )

    assert (
        ranking[1].rank
        == 2
    )
