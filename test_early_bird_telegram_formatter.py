from datetime import datetime, timedelta, timezone

from app.domain.candle import Candle
from app.intelligence.early_bird.scanner import EarlyBirdScanner
from app.telegram.early_bird_formatter import (
    format_early_bird_shadow_preview,
)


NOW = datetime(
    2026,
    8,
    2,
    7,
    0,
    tzinfo=timezone.utc,
)


class FakeCandleSource:
    def source_name(self):
        return "fake-public-candles"

    def get_candles(
        self,
        asset,
        interval,
        start_time,
        end_time=None,
        limit=1000,
    ):
        del interval, start_time, end_time

        candles = []

        for index in range(limit):
            price = 100.0 + index * 0.01

            candles.append(
                Candle(
                    timestamp=(
                        NOW
                        - timedelta(
                            minutes=15 * (limit - index)
                        )
                    ),
                    open=price,
                    high=price * 1.01,
                    low=price * 0.99,
                    close=price,
                    volume=(
                        100.0
                        if index < limit - 1
                        else 300.0
                    ),
                )
            )

        return candles


class FakeFundingService:
    def build(self, asset):
        return {
            "status": "unavailable",
            "asset": asset,
            "exchanges": {},
            "unavailable_exchanges": {},
            "captured_at": NOW.isoformat(),
        }


def build_scan():
    return EarlyBirdScanner(
        candle_source=FakeCandleSource(),
        funding_service=FakeFundingService(),
    ).scan(
        ("BTC", "ETH"),
        timeframe="15m",
        candle_count=100,
        limit=2,
        timestamp=NOW,
    )


def test_formatter_marks_output_as_shadow_read_only() -> None:
    output = format_early_bird_shadow_preview(
        build_scan()
    )

    assert "🧪 <b>Early Bird Live Test</b>" in output
    assert "<b>SHADOW / READ-ONLY</b>" in output
    assert "Production influence: NO" in output


def test_formatter_contains_scan_summary() -> None:
    output = format_early_bird_shadow_preview(
        build_scan()
    )

    assert "Timeframe: 15m" in output
    assert "Successful: 2" in output
    assert "Failed: 0" in output


def test_formatter_contains_ranked_assets_and_scores() -> None:
    output = format_early_bird_shadow_preview(
        build_scan()
    )

    assert "<b>1. " in output
    assert "<b>2. " in output
    assert "Opportunity:" in output
    assert "Priority:" in output
    assert "Maturity:" in output
    assert "Quality:" in output


def test_formatter_contains_funding_and_open_interest_states() -> None:
    output = format_early_bird_shadow_preview(
        build_scan()
    )

    assert "Funding: MISSING" in output
    assert "OI change: MISSING" in output


def test_formatter_escapes_html_in_errors() -> None:
    scan = build_scan()

    from dataclasses import replace

    modified = replace(
        scan,
        items=scan.items[:1],
        errors={
            "ETH": "Provider <offline> & unavailable",
        },
        successful_assets=("BTC",),
        failed_assets=("ETH",),
    )

    output = format_early_bird_shadow_preview(
        modified
    )

    assert (
        "Provider &lt;offline&gt; "
        "&amp; unavailable"
    ) in output
    assert "Provider <offline>" not in output


def test_formatter_rejects_invalid_scan() -> None:
    import pytest

    with pytest.raises(
        TypeError,
        match="scan must be an EarlyBirdScanResult",
    ):
        format_early_bird_shadow_preview({})
