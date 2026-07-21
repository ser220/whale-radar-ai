from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .models import PaperTrade


class PaperExecutionService:
    """
    Simulated execution boundary.

    Creates paper trades only.
    No exchange access.
    """

    def open_trade(
        self,
        symbol: str,
        side: str,
        price: float,
        quantity: float,
    ) -> PaperTrade:

        return PaperTrade(
            trade_id=str(
                uuid4()
            ),
            symbol=symbol,
            side=side,
            entry_price=price,
            quantity=quantity,
            opened_at=datetime.now(
                timezone.utc
            ),
            status="OPEN",
        )
