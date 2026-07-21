from datetime import datetime, timezone

import pytest

from app.execution import (
    PaperExecutionService,
    PaperTrade,
)


def test_paper_trade_creation():
    trade = PaperTrade(
        trade_id="trade-001",
        symbol="BTCUSDT",
        side="LONG",
        entry_price=65000.0,
        quantity=0.01,
        opened_at=datetime.now(
            timezone.utc
        ),
        status="OPEN",
    )

    assert (
        trade.trade_id
        == "trade-001"
    )

    assert (
        trade.symbol
        == "BTCUSDT"
    )

    assert (
        trade.side
        == "LONG"
    )

    assert (
        trade.status
        == "OPEN"
    )


def test_paper_execution_opens_trade():
    service = PaperExecutionService()

    trade = service.open_trade(
        symbol="BTCUSDT",
        side="LONG",
        price=65000.0,
        quantity=0.01,
    )

    assert isinstance(
        trade,
        PaperTrade,
    )

    assert (
        trade.symbol
        == "BTCUSDT"
    )

    assert (
        trade.entry_price
        == 65000.0
    )

    assert (
        trade.quantity
        == 0.01
    )

    assert (
        trade.status
        == "OPEN"
    )

    assert (
        trade.trade_id
    )


def test_invalid_trade_rejected():
    with pytest.raises(ValueError):
        PaperTrade(
            trade_id="",
            symbol="BTCUSDT",
            side="LONG",
            entry_price=65000.0,
            quantity=0.01,
            opened_at=datetime.now(
                timezone.utc
            ),
            status="OPEN",
        )
