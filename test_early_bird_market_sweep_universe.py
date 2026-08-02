from app.data.market.static_market_universe_provider import (
    StaticMarketUniverseProvider,
)
from app.intelligence.early_bird.market_sweep import (
    EarlyBirdMarketSweep,
)


class FakeScanner:
    def scan(
        self,
        assets,
        timeframe="15m",
        limit=5,
    ):
        class Candidate:
            def __init__(self, asset, quality):
                self.asset = asset
                self.quality = quality

        class Build:
            def __init__(self, candidate):
                self.candidate = candidate

        class Item:
            def __init__(self, candidate):
                self.build_result = Build(candidate)

        return type(
            "Result",
            (),
            {
                "items": (
                    Item(Candidate("BTC", 70)),
                    Item(Candidate("HYPE", 90)),
                )
            },
        )()


def test_market_sweep_works_with_universe_provider():
    provider = StaticMarketUniverseProvider(
        assets=(
            "BTC",
            "HYPE",
        )
    )

    universe = provider.build()

    sweep = EarlyBirdMarketSweep(
        scanner=FakeScanner(),
    )

    result = sweep.candidates(
        universe.assets,
    )

    assert [
        item.asset
        for item in result
    ] == [
        "HYPE",
        "BTC",
    ]
