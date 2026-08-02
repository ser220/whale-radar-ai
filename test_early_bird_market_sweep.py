from datetime import datetime, timezone

from app.data.market.market_universe import (
    MarketUniverse,
)
from app.intelligence.early_bird.market_sweep import (
    EarlyBirdMarketSweep,
)


NOW = datetime(
    2026,
    8,
    2,
    8,
    0,
    tzinfo=timezone.utc,
)


class FakeScanner:
    def __init__(self):
        self.assets = None

    def scan(
        self,
        assets,
        timeframe="15m",
        limit=5,
    ):
        self.assets = assets
        return {
            "assets": assets,
            "timeframe": timeframe,
            "limit": limit,
        }


def test_market_sweep_requires_scanner():
    import pytest

    with pytest.raises(
        TypeError,
        match="scanner must provide scan",
    ):
        EarlyBirdMarketSweep(
            scanner=None,
        )


def test_market_sweep_accepts_universe():
    scanner = FakeScanner()

    sweep = EarlyBirdMarketSweep(
        scanner=scanner,
    )

    result = sweep.universe(
        MarketUniverse(
            assets=("BTC", "ETH"),
        )
    )

    assert result["assets"] == (
        "BTC",
        "ETH",
    )

    assert scanner.assets == (
        "BTC",
        "ETH",
    )
