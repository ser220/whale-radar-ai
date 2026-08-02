from datetime import datetime, timezone

from app.intelligence.early_bird.runtime import (
    EarlyBirdRuntime,
)


def test_multi_asset_cascade_pool_selects_best_candidate():

    runtime = EarlyBirdRuntime()

    assets = (
        {
            "asset": "BTC",
            "long_score": 70,
            "short_score": 20,
        },
        {
            "asset": "ETH",
            "long_score": 55,
            "short_score": 30,
        },
        {
            "asset": "HYPE",
            "long_score": 85,
            "short_score": 20,
        },
        {
            "asset": "SOL",
            "long_score": 40,
            "short_score": 50,
        },
    )

    opportunities = []

    for item in assets:

        result = runtime.process_cascade_pipeline(
            asset=item["asset"],
            long_score=item["long_score"],
            short_score=item["short_score"],
        )

        if result.opportunity:
            opportunities.append(
                result.opportunity
            )

    assert len(opportunities) > 0

    best = sorted(
        opportunities,
        key=lambda item: item.score,
        reverse=True,
    )[0]

    assert best.asset == "HYPE"
    assert best.direction == "LONG"
    assert best.rank == "L4"
