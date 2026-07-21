from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PaperTradeResult:
    """
    Immutable closed paper trade result.

    Contains lifecycle outcome only.
    No strategy logic.
    """

    trade_id: str
    symbol: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    closed_at: datetime
    status: str

    def __post_init__(self) -> None:
        trade_id = self.trade_id.strip()
        symbol = self.symbol.strip()
        status = self.status.strip()

        if not trade_id:
            raise ValueError(
                "trade_id is required"
            )

        if not symbol:
            raise ValueError(
                "symbol is required"
            )

        if self.entry_price <= 0:
            raise ValueError(
                "entry_price must be positive"
            )

        if self.exit_price <= 0:
            raise ValueError(
                "exit_price must be positive"
            )

        if self.quantity <= 0:
            raise ValueError(
                "quantity must be positive"
            )

        if not status:
            raise ValueError(
                "status is required"
            )

        object.__setattr__(
            self,
            "trade_id",
            trade_id,
        )

        object.__setattr__(
            self,
            "symbol",
            symbol,
        )

        object.__setattr__(
            self,
            "status",
            status,
        )
