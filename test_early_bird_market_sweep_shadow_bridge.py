from datetime import datetime, timezone
from types import SimpleNamespace

from app.intelligence.early_bird.market_sweep_result import (
    EarlyBirdMarketSweepResult,
)
from app.intelligence.early_bird.market_sweep_shadow_bridge import (
    process_market_sweep_shadow,
)


def test_market_sweep_result_is_forwarded_to_shadow_pipeline():
    calls = []

    def fake_process(*, asset, payload):
        calls.append(
            {
                "asset": asset,
                "payload": payload,
            }
        )
        return "OK"

    result = EarlyBirdMarketSweepResult(
        items=(
            SimpleNamespace(
                asset="BTC",
                quality=90,
            ),
        ),
        scanned_assets=("BTC",),
        generated_at=datetime(
            2026,
            8,
            2,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )

    output = process_market_sweep_shadow(
        result,
        process_fn=fake_process,
    )

    assert output == [
        "OK",
    ]

    assert calls[0]["asset"] == "BTC"
