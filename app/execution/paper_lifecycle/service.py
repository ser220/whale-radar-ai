from __future__ import annotations

from datetime import datetime, timezone

from app.execution import PaperTrade

from .models import PaperTradeResult


class PaperTradeLifecycleService:
    """
    Manages paper trade lifecycle.

    No exchange access.
    No real execution.
    """

    def close_trade(
        self,
        trade: PaperTrade,
        exit_price: float,
    ) -> PaperTradeResult:

        if not isinstance(
            trade,
            PaperTrade,
        ):
            raise TypeError(
                "trade must be PaperTrade"
            )

        if exit_price <= 0:
            raise ValueError(
                "exit_price must be positive"
            )

        pnl = (
            (
                exit_price
                -
                trade.entry_price
            )
            /
            trade.entry_price
        )

        if trade.side.upper() == "SHORT":
            pnl = -pnl

        return PaperTradeResult(
            trade_id=trade.trade_id,
            symbol=trade.symbol,
            entry_price=trade.entry_price,
            exit_price=exit_price,
            quantity=trade.quantity,
            pnl=round(
                pnl,
                6,
            ),
            closed_at=datetime.now(
                timezone.utc
            ),
            status="CLOSED",
        )
