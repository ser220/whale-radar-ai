from app.backtest.evaluation import (
    BacktestEvaluationEvaluator,
    BacktestEvaluationReport,
)

from app.backtest.performance import (
    BacktestPerformanceReport,
)

from app.backtest.analytics import (
    BacktestAnalyticsReport,
)

from app.backtest.equity import (
    BacktestEquityCurve,
)

from app.backtest.risk import (
    BacktestRiskReport,
)

from app.backtest.benchmark import (
    BacktestBenchmarkReport,
)


def test_backtest_evaluation():

    report = (
        BacktestEvaluationEvaluator()
        .evaluate(
            performance=BacktestPerformanceReport(
                total_trades=10,
                winning_trades=7,
                losing_trades=3,
                total_pnl=1000.0,
                average_pnl=100.0,
                win_rate=0.7,
                profit_factor=3.0,
            ),
            analytics=BacktestAnalyticsReport(
                total_return=0.10,
                average_trade=100.0,
                win_rate=0.7,
                profit_factor=3.0,
                total_trades=10,
            ),
            equity=BacktestEquityCurve(
                points=(),
                initial_balance=10000.0,
                final_equity=11000.0,
                cumulative_return=0.10,
                peak_equity=11000.0,
                max_drawdown=200.0,
            ),
            risk=BacktestRiskReport(
                max_drawdown=200.0,
                max_drawdown_percent=0.018,
                recovery_factor=5.0,
                risk_score=0.982,
            ),
            benchmark=BacktestBenchmarkReport(
                strategy_return=0.10,
                benchmark_return=0.03,
                alpha=0.07,
                outperformance=0.07,
                benchmark_win=True,
            ),
        )
    )

    assert isinstance(
        report,
        BacktestEvaluationReport,
    )

    assert (
        report.quality_rating
        == "C"
    )

    assert (
        report.recommendation
        == "REVIEW"
    )

    assert round(
        report.overall_score,
        1,
    ) == 55.2
