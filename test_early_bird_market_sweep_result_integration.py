from datetime import datetime, timezone
from types import SimpleNamespace

from app.intelligence.early_bird.market_sweep import (
    EarlyBirdMarketSweep,
)
from app.intelligence.early_bird.market_sweep_result import (
    EarlyBirdMarketSweepResult,
)


NOW = datetime(
    2026,
    8,
    2,
    10,
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
                            asset="BTC",
                            quality=70,
                        )
                    )
                ),
            ),
            completed_at=NOW,
        )


def test_market_sweep_returns_result_contract():
    sweep = EarlyBirdMarketSweep(
        scanner=FakeScanner(),
    )

    result = sweep.run(
        ("BTC",),
    )

    assert isinstance(
        result,
        EarlyBirdMarketSweepResult,
    )

    assert result.scanned_assets == (
        "BTC",
    )
