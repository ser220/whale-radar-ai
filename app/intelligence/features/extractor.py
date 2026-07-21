from __future__ import annotations

from app.intelligence.market import (
    MarketSnapshot,
)

from .models import MarketFeatures


class MarketFeatureExtractor:
    """
    Converts MarketSnapshot into MarketFeatures.

    Feature calculation only.
    No decision logic allowed.
    """

    @staticmethod
    def extract(
        snapshot: MarketSnapshot,
    ) -> MarketFeatures:

        if not isinstance(
            snapshot,
            MarketSnapshot,
        ):
            raise TypeError(
                "snapshot must be MarketSnapshot"
            )

        trend = (
            "bullish"
            if snapshot.price > 0
            else "unknown"
        )

        volatility_state = (
            "high"
            if snapshot.volatility > 0.05
            else "normal"
        )

        liquidity_state = (
            "healthy"
            if snapshot.volume_24h > 0
            else "unknown"
        )

        return MarketFeatures(
            symbol=snapshot.symbol,
            trend=trend,
            volatility_state=(
                volatility_state
            ),
            liquidity_state=(
                liquidity_state
            ),
        )
