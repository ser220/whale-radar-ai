from types import SimpleNamespace

from app.intelligence.early_bird.market_sweep import (
    EarlyBirdMarketSweep,
)


class FakeScanner:
    def scan(self, assets, timeframe="15m", limit=5):
        return None


def test_market_sweep_ranks_candidates_by_quality():
    sweep = EarlyBirdMarketSweep(
        scanner=FakeScanner(),
    )

    candidates = (
        SimpleNamespace(
            asset="BTC",
            quality=70,
        ),
        SimpleNamespace(
            asset="HYPE",
            quality=90,
        ),
        SimpleNamespace(
            asset="LINK",
            quality=80,
        ),
    )

    ranked = sweep.rank(candidates)

    assert [
        item.asset
        for item in ranked
    ] == [
        "HYPE",
        "LINK",
        "BTC",
    ]
