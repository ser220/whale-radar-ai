from datetime import datetime, timezone

import pytest

from app.intelligence.early_bird.market_sweep_result import (
    EarlyBirdMarketSweepResult,
)


NOW = datetime(
    2026,
    8,
    2,
    9,
    0,
    tzinfo=timezone.utc,
)


def test_empty_result_is_allowed():
    result = EarlyBirdMarketSweepResult(
        items=(),
        scanned_assets=(),
        generated_at=NOW,
    )

    assert result.items == ()
    assert result.scanned_assets == ()
    assert result.generated_at == NOW


def test_result_requires_timezone_datetime():
    with pytest.raises(
        ValueError,
        match="generated_at must be timezone aware",
    ):
        EarlyBirdMarketSweepResult(
            items=(),
            scanned_assets=(),
            generated_at=datetime(
                2026,
                8,
                2,
                9,
                0,
            ),
        )
