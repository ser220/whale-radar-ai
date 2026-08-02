from datetime import datetime, timedelta, timezone
import importlib

import pytest

from app.domain.candle import Candle
from app.intelligence.early_bird import (
    FactorAvailability,
)
from app.intelligence.early_bird.scanner import (
    EarlyBirdScanner,
)
from run_early_bird_open_interest_demo import (
    format_open_interest_comparison,
    run_two_scan_open_interest,
)


NOW = datetime(
    2026,
    8,
    2,
    0,
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

        values = []

        for index in range(limit):
            price = 100.0 + index * 0.01

            values.append(
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
                    volume=100.0,
                )
            )

        return values


class FakeFundingService:
    def build(self, asset):
        return {
            "status": "unavailable",
            "asset": asset,
            "exchanges": {},
            "unavailable_exchanges": {},
            "captured_at": NOW.isoformat(),
        }


class FakeOpenInterestService:
    def __init__(self):
        self.calls = 0

    def build(self, asset):
        captured_at = (
            NOW
            + timedelta(minutes=15 * self.calls)
        )
        total = (
            16_000_000_000
            if self.calls == 0
            else 16_800_000_000
        )
        self.calls += 1

        return {
            "status": "completed",
            "asset": asset,
            "exchange_count": 4,
            "analytics": {
                "total_open_interest_usd": total,
                "execution_open_interest_usd": (
                    total * 0.75
                ),
                "largest_market": {
                    "exchange": "Binance",
                },
            },
            "captured_at": (
                captured_at.isoformat()
            ),
        }


def build_scanner():
    from app.data.market import OpenInterestHistory
    from app.intelligence.early_bird.scanner import (
        OpenInterestChangeFactor,
    )

    return EarlyBirdScanner(
        candle_source=FakeCandleSource(),
        funding_service=FakeFundingService(),
        open_interest_service=(
            FakeOpenInterestService()
        ),
        open_interest_history=(
            OpenInterestHistory()
        ),
        open_interest_calculator=(
            OpenInterestChangeFactor()
        ),
    )


def test_two_scan_helper_uses_fake_wait() -> None:
    waits = []

    first, second = run_two_scan_open_interest(
        scanner=build_scanner(),
        assets=("BTC",),
        timeframe="15m",
        candle_count=100,
        limit=1,
        interval_seconds=900,
        sleep_fn=waits.append,
        clock_fn=iter(
            (
                NOW,
                NOW + timedelta(minutes=15),
            )
        ).__next__,
    )

    assert waits == [900.0]

    first_factor = (
        first.items[0]
        .build_result
        .factor_values["open_interest_change"]
    )
    second_factor = (
        second.items[0]
        .build_result
        .factor_values["open_interest_change"]
    )

    assert (
        first_factor.availability
        is FactorAvailability.MISSING
    )
    assert (
        second_factor.availability
        is FactorAvailability.AVAILABLE
    )
    assert second_factor.score == 50.0
    assert (
        second_factor.metadata["change_percent"]
        == 5.0
    )


def test_formatter_contains_factor_states() -> None:
    first, second = run_two_scan_open_interest(
        scanner=build_scanner(),
        assets=("BTC",),
        timeframe="15m",
        candle_count=100,
        limit=1,
        interval_seconds=0,
        sleep_fn=lambda value: None,
        clock_fn=iter(
            (
                NOW,
                NOW + timedelta(minutes=15),
            )
        ).__next__,
    )

    output = format_open_interest_comparison(
        first,
        second,
    )

    assert "Asset: BTC" in output
    assert "First OI factor: MISSING" in output
    assert "Second OI factor: AVAILABLE" in output
    assert "Change: 5.0%" in output


@pytest.mark.parametrize(
    "value",
    (True, False, "900", None),
)
def test_interval_requires_numeric_value(value) -> None:
    with pytest.raises(
        TypeError,
        match="interval_seconds must be numeric",
    ):
        run_two_scan_open_interest(
            scanner=build_scanner(),
            interval_seconds=value,
        )


def test_negative_interval_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "interval_seconds must not be negative"
        ),
    ):
        run_two_scan_open_interest(
            scanner=build_scanner(),
            interval_seconds=-1,
        )


def test_scanner_boundary_is_required() -> None:
    with pytest.raises(
        TypeError,
        match="scanner must provide scan",
    ):
        run_two_scan_open_interest(
            scanner=object(),
        )


def test_demo_is_import_safe() -> None:
    module = importlib.import_module(
        "run_early_bird_open_interest_demo"
    )

    assert callable(module.main)
