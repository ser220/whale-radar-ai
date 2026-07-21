from datetime import datetime, timezone

import pytest

from app.execution import (
    PaperExecutionService,
    PaperTrade,
)

from app.execution.paper_lifecycle import (
    PaperTradeResult,
    PaperTradeLifecycleService,
)


def create_trade(
    side="LONG",
):
    service = PaperExecutionService()

    return service.open_trade(
        symbol="BTCUSDT",
        side=side,
        price=65000.0,
        quantity=0.01,
    )


def test_trade_result_creation():
    result = PaperTradeResult(
        trade_id="trade-001",
        symbol="BTCUSDT",
        entry_price=65000.0,
        exit_price=67000.0,
        quantity=0.01,
        pnl=0.030769,
        closed_at=datetime.now(
            timezone.utc
        ),
        status="CLOSED",
    )

    assert (
        result.symbol
        == "BTCUSDT"
    )

    assert (
        result.status
        == "CLOSED"
    )


def test_long_trade_close_profit():
    trade = create_trade()

    lifecycle = (
        PaperTradeLifecycleService()
    )

    result = lifecycle.close_trade(
        trade,
        exit_price=67000.0,
    )

    assert isinstance(
        result,
        PaperTradeResult,
    )

    assert (
        result.pnl
        > 0
    )

    assert (
        result.status
        == "CLOSED"
    )


def test_long_trade_close_loss():
    trade = create_trade()

    lifecycle = (
        PaperTradeLifecycleService()
    )

    result = lifecycle.close_trade(
        trade,
        exit_price=63000.0,
    )

    assert (
        result.pnl
        < 0
    )


def test_short_trade_profit():
    trade = create_trade(
        side="SHORT",
    )

    lifecycle = (
        PaperTradeLifecycleService()
    )

    result = lifecycle.close_trade(
        trade,
        exit_price=63000.0,
    )

    assert (
        result.pnl
        > 0
    )


def test_invalid_trade_rejected():
    lifecycle = (
        PaperTradeLifecycleService()
    )

    with pytest.raises(TypeError):
        lifecycle.close_trade(
            "invalid",
            67000.0,
        )
