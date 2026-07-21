from datetime import datetime, timezone

import pytest

from app.execution.paper_lifecycle import (
    PaperTradeResult,
)

from app.performance import (
    PerformanceReport,
    PaperPerformanceTracker,
)


def create_result(
    pnl: float,
) -> PaperTradeResult:

    return PaperTradeResult(
        trade_id=f"trade-{pnl}",
        symbol="BTCUSDT",
        entry_price=65000.0,
        exit_price=67000.0,
        quantity=0.01,
        pnl=pnl,
        closed_at=datetime.now(
            timezone.utc
        ),
        status="CLOSED",
    )


def test_performance_report_creation():
    report = PerformanceReport(
        total_trades=10,
        winning_trades=6,
        losing_trades=4,
        total_pnl=0.25,
        average_pnl=0.025,
        win_rate=0.6,
    )

    assert (
        report.total_trades
        == 10
    )

    assert (
        report.win_rate
        == 0.6
    )


def test_tracker_calculates_metrics():
    tracker = PaperPerformanceTracker()

    trades = [
        create_result(0.05),
        create_result(0.02),
        create_result(-0.01),
        create_result(-0.02),
    ]

    report = tracker.calculate(
        trades
    )

    assert isinstance(
        report,
        PerformanceReport,
    )

    assert (
        report.total_trades
        == 4
    )

    assert (
        report.winning_trades
        == 2
    )

    assert (
        report.losing_trades
        == 2
    )

    assert (
        report.win_rate
        == 0.5
    )

    assert (
        report.total_pnl
        == 0.04
    )


def test_empty_trade_list():
    tracker = PaperPerformanceTracker()

    report = tracker.calculate(
        []
    )

    assert (
        report.total_trades
        == 0
    )

    assert (
        report.win_rate
        == 0
    )


def test_invalid_trade_type_rejected():
    tracker = PaperPerformanceTracker()

    with pytest.raises(TypeError):
        tracker.calculate(
            ["invalid"]
        )
