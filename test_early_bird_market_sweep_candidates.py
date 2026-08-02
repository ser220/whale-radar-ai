from types import SimpleNamespace

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
                SimpleNamespace(
                    build_result=SimpleNamespace(
                        candidate=SimpleNamespace(
                            asset="HYPE",
                            quality=90,
                        )
                    )
                ),
            )
        )


def test_market_sweep_extracts_and_ranks_candidates():
    sweep = EarlyBirdMarketSweep(
        scanner=FakeScanner(),
    )

    result = sweep.candidates(
        ("BTC", "HYPE"),
    )

    assert [
        item.asset
        for item in result
    ] == [
        "HYPE",
        "BTC",
    ]
