from datetime import datetime, timezone
from types import SimpleNamespace

from app.data.market.market_universe import (
    MarketUniverse,
)

from app.intelligence.early_bird.market_sweep import (
    EarlyBirdMarketSweep,
)

from app.intelligence.early_bird.runtime import (
    EarlyBirdRuntime,
)


NOW = datetime(
    2026,
    8,
    2,
    12,
    0,
    tzinfo=timezone.utc,
)


class FakeScanner:

    def scan(
        self,
        assets,
        timeframe="15m",
        limit=5,
    ):

        return SimpleNamespace(
            items=(
                SimpleNamespace(
                    build_result=SimpleNamespace(
                        candidate=SimpleNamespace(
                            asset="HYPE",
                            quality=85,
                        )
                    )
                ),
            ),
            completed_at=NOW,
        )


def test_market_universe_flows_into_perpetual_pipeline():

    universe = MarketUniverse(
        assets=(
            "BTC",
            "ETH",
            "HYPE",
        ),
    )

    sweep = EarlyBirdMarketSweep(
        scanner=FakeScanner(),
    )

    sweep_result = sweep.run(
        universe.assets,
    )

    runtime = EarlyBirdRuntime()

    result = runtime.process_cascade_pipeline(
        asset=sweep_result.items[0].asset,
        long_score=85,
        short_score=20,
    )

    assert result.opportunity.asset == "HYPE"
    assert result.opportunity.direction == "LONG"

