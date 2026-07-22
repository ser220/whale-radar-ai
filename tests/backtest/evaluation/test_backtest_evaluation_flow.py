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


def test_full_backtest_evaluation_flow():

    performance = BacktestPerformanceReport(
        total_trades=20,
        winning_trades=14,
        losing_trades=6,
        total_pnl=1500.0,
        average_pnl=75.0,
        win_rate=0.7,
        profit_factor=2.8,
    )

    analytics = BacktestAnalyticsReport(
        total_return=0.15,
        average_trade=75.0,
        win_rate=0.7,
        profit_factor=2.8,
        total_trades=20,
    )

    equity = BacktestEquityCurve(
        points=(),
        initial_balance=10000.0,
        final_equity=11500.0,
        cumulative_return=0.15,
        peak_equity=11600.0,
        max_drawdown=100.0,
    )

    risk = BacktestRiskReport(
        max_drawdown=100.0,
        max_drawdown_percent=0.0086,
        recovery_factor=15.0,
        risk_score=0.9914,
    )

    benchmark = BacktestBenchmarkReport(
        strategy_return=0.15,
        benchmark_return=0.05,
        alpha=0.10,
        outperformance=0.10,
        benchmark_win=True,
    )

    report = (
        BacktestEvaluationEvaluator()
        .evaluate(
            performance,
            analytics,
            equity,
            risk,
            benchmark,
        )
    )

    assert isinstance(
        report,
        BacktestEvaluationReport,
    )

    assert (
        report.benchmark.benchmark_win
        is True
    )

    assert (
        report.risk.max_drawdown
        == 100.0
    )

    assert (
        report.performance.total_pnl
        == 1500.0
    )

    assert round(
        report.overall_score,
        2,
    ) == 59.14

    assert (
        report.recommendation
        == "REVIEW"
    )
