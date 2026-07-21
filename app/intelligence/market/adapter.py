from __future__ import annotations

from datetime import datetime, timezone

from .models import MarketSnapshot


class MarketIntelligenceAdapter:
    """
    Boundary for external market data providers.

    No trading decisions allowed.
    """

    def snapshot(
        self,
        symbol: str,
        price: float,
        volume_24h: float,
        volatility: float,
    ) -> MarketSnapshot:

        return MarketSnapshot(
            symbol=symbol,
            price=price,
            volume_24h=volume_24h,
            volatility=volatility,
            captured_at=datetime.now(
                timezone.utc
            ),
        )
