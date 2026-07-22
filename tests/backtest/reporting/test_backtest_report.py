from datetime import datetime, timezone

from app.backtest import (
    BacktestReport,
    BacktestReportGenerator,
    BacktestSessionConfig,
    BacktestSessionResult,
    BacktestPerformanceReport,
)


def build_session_result():

    now = datetime.now(
        timezone.utc
    )

    config = BacktestSessionConfig(
        symbol="BTCUSDT",
        start_time=now,
        end_time=now,
        initial_balance=10000.0,
    )

    return BacktestSessionResult(
        config=config,
        processed_snapshots=100,
        generated_trades=5,
        started_at=now,
        finished_at=now,
    )


def build_performance_report():

    return BacktestPerformanceReport(
        total_trades=5,
        winning_trades=3,
        losing_trades=2,
        total_pnl=150.0,
        average_pnl=30.0,
        win_rate=0.6,
        profit_factor=2.5,
    )


def test_backtest_report_model():

    report = BacktestReport(
        session=build_session_result(),
        performance=build_performance_report(),
    )

    assert (
        report.session.generated_trades
        == 5
    )

    assert (
        report.performance.win_rate
        == 0.6
    )


def test_backtest_report_generator():

    generator = BacktestReportGenerator()

    report = generator.generate(
        build_session_result(),
        build_performance_report(),
    )

    assert isinstance(
        report,
        BacktestReport,
    )

    assert (
        report.session.config.symbol
        == "BTCUSDT"
    )
