"""Offline funding divergence and scanner integration tests for PS-3 Step 2."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import unittest

from app.domain.candle import Candle
from app.intelligence.early_bird import FactorAvailability
from app.intelligence.early_bird.scanner import (
    EarlyBirdScanner,
    FundingDivergenceFactor,
    format_scan_result,
)


UTC = timezone.utc
NOW = datetime(2026, 7, 15, 18, 0, tzinfo=UTC)
INTERVAL = timedelta(minutes=15)


def venue(name, value, observed_at=None):
    return {
        "exchange_name": name.title(),
        "funding_percent": value,
        "observed_at": (observed_at or NOW - timedelta(minutes=2)).isoformat(),
        "status": "completed",
    }


def funding_result(exchanges=None, errors=None, **overrides):
    payload = {
        "status": "completed",
        "asset": "BTC",
        "exchanges": exchanges or {},
        "unavailable_exchanges": errors or {},
        "captured_at": (NOW - timedelta(minutes=1)).isoformat(),
    }
    payload.update(overrides)
    return payload


def factor(result, asset="BTC", evaluated_at=NOW):
    return FundingDivergenceFactor().build(
        asset,
        result,
        evaluated_at=evaluated_at,
    )


def candles(asset, count=100):
    base = 100.0 + len(asset)
    rows = []
    for index in range(count):
        price = base + index * 0.01
        rows.append(
            Candle(
                timestamp=NOW - INTERVAL * (count - index),
                open=price,
                high=price * 1.01,
                low=price * 0.99,
                close=price,
                volume=100.0 + (300.0 if index == count - 1 else 0.0),
            )
        )
    return rows


class FakeCandleSource:
    def __init__(self, failures=()):
        self.failures = set(failures)

    def source_name(self):
        return "fake-binance-public-spot"

    def get_candles(self, asset, interval, start_time, end_time=None, limit=1000):
        del interval, start_time, end_time, limit
        normalized = asset.upper().replace("USDT", "")
        if normalized in self.failures:
            raise RuntimeError("candle fixture failed")
        return candles(normalized)


class FakeFundingService:
    def __init__(self, results=None, failures=()):
        self.results = results or {}
        self.failures = set(failures)
        self.calls = []

    def build(self, asset):
        normalized = asset.upper().replace("USDT", "")
        self.calls.append(normalized)
        if normalized in self.failures:
            raise RuntimeError("https://provider.test?token=secret")
        return self.results.get(
            normalized,
            funding_result(
                {
                    "binance": venue("binance", 0.01),
                    "okx": venue("okx", 0.011),
                }
            ),
        )


def scanner_result(assets=("BTC",), funding_service=None, candle_source=None):
    scanner = EarlyBirdScanner(
        candle_source=candle_source or FakeCandleSource(),
        funding_service=funding_service or FakeFundingService(),
    )
    return scanner.scan(
        assets,
        timeframe="15m",
        candle_count=100,
        limit=10,
        timestamp=NOW,
    )


class FundingDivergenceFactorTests(unittest.TestCase):
    def test_two_fresh_venues_are_available(self):
        value = factor(
            funding_result(
                {
                    "binance": venue("binance", 0.01),
                    "okx": venue("okx", 0.03),
                }
            )
        )
        self.assertIs(FactorAvailability.AVAILABLE, value.availability)
        self.assertEqual(2, value.metadata["venue_count"])

    def test_mixed_sign_bonus(self):
        aligned = factor(
            funding_result(
                {
                    "binance": venue("binance", 0.01),
                    "okx": venue("okx", 0.03),
                }
            )
        )
        mixed = factor(
            funding_result(
                {
                    "binance": venue("binance", -0.01),
                    "okx": venue("okx", 0.01),
                }
            )
        )
        self.assertEqual(round(aligned.score + 15.0, 6), mixed.score)
        self.assertTrue(mixed.metadata["mixed_sign"])

    def test_low_spread_scores_zero(self):
        value = factor(
            funding_result(
                {
                    "binance": venue("binance", 0.010),
                    "okx": venue("okx", 0.015),
                }
            )
        )
        self.assertEqual(0.0, value.score)

    def test_high_spread_is_capped(self):
        value = factor(
            funding_result(
                {
                    "binance": venue("binance", -0.10),
                    "okx": venue("okx", 0.10),
                }
            )
        )
        self.assertEqual(100.0, value.score)

    def test_hub_percentage_units_are_not_multiplied_again(self):
        value = factor(
            funding_result(
                {
                    "binance": venue("binance", 0.00),
                    "okx": venue("okx", 0.10),
                }
            )
        )
        self.assertEqual(100.0, value.score)
        self.assertEqual("percentage_points", value.metadata["funding_unit"])

    def test_one_venue_is_missing(self):
        value = factor(
            funding_result({"binance": venue("binance", 0.01)})
        )
        self.assertIs(FactorAvailability.MISSING, value.availability)
        self.assertIsNone(value.score)

    def test_stale_only_values_are_stale(self):
        old = NOW - timedelta(minutes=16)
        value = factor(
            funding_result(
                {
                    "binance": venue("binance", 0.01, old),
                    "okx": venue("okx", 0.02, old),
                }
            )
        )
        self.assertIs(FactorAvailability.STALE, value.availability)
        self.assertIsNone(value.score)

    def test_all_failures_are_error(self):
        value = factor(
            funding_result({}, {"binance": "secret", "okx": "failed"})
        )
        self.assertIs(FactorAvailability.ERROR, value.availability)
        self.assertIsNone(value.score)

    def test_explicit_unsupported_state(self):
        value = factor(funding_result(status="unsupported"))
        self.assertIs(FactorAvailability.UNSUPPORTED, value.availability)

    def test_partial_failure_remains_available(self):
        value = factor(
            funding_result(
                {
                    "binance": venue("binance", 0.01),
                    "okx": venue("okx", 0.02),
                },
                {"gate": "failure"},
            )
        )
        self.assertIs(FactorAvailability.AVAILABLE, value.availability)
        self.assertEqual(("gate",), tuple(value.metadata["venue_errors"]))

    def test_partial_failure_reduces_quality(self):
        rows = {
            "binance": venue("binance", 0.01),
            "okx": venue("okx", 0.02),
        }
        full = factor(funding_result(rows))
        partial = factor(funding_result(rows, {"gate": "failure"}))
        self.assertLess(partial.quality, full.quality)
        self.assertLess(full.quality, 100.0)

    def test_oldest_fresh_timestamp_is_observed_at(self):
        oldest = NOW - timedelta(minutes=10)
        value = factor(
            funding_result(
                {
                    "binance": venue("binance", 0.01, NOW - timedelta(minutes=2)),
                    "okx": venue("okx", 0.02, oldest),
                }
            )
        )
        self.assertEqual(oldest, value.observed_at)

    def test_metadata_contains_immutable_venue_provenance(self):
        value = factor(
            funding_result(
                {
                    "binance": venue("binance", 0.01),
                    "okx": venue("okx", 0.02),
                }
            )
        )
        self.assertEqual(("Binance", "Okx"), value.metadata["used_venues"])
        with self.assertRaises(TypeError):
            value.metadata["venue_count"] = 3
        with self.assertRaises(FrozenInstanceError):
            value.score = 0

    def test_factor_has_no_direction_or_trade_fields(self):
        payload = factor(
            funding_result(
                {
                    "binance": venue("binance", 0.01),
                    "okx": venue("okx", 0.02),
                }
            )
        ).to_dict()
        forbidden = {"direction", "buy", "sell", "entry", "tp", "sl"}
        self.assertTrue(forbidden.isdisjoint(payload))

    def test_error_metadata_is_sanitized(self):
        value = factor(
            funding_result(
                {},
                {"binance": "https://host/path?token=secret"},
            )
        )
        serialized = str(value.to_dict())
        self.assertNotIn("secret", serialized)
        self.assertNotIn("https://", serialized)


class FundingScannerIntegrationTests(unittest.TestCase):
    def test_scanner_calls_funding_once_per_asset(self):
        service = FakeFundingService()
        scanner_result(("BTC", "ETH", "SOL"), service)
        self.assertEqual(["BTC", "ETH", "SOL"], service.calls)

    def test_funding_failure_does_not_abort_candle_scan(self):
        result = scanner_result(
            ("BTC",),
            FakeFundingService(failures=("BTC",)),
        )
        self.assertEqual(("BTC",), result.successful_assets)
        funding = result.items[0].build_result.factor_values["funding_divergence"]
        self.assertIs(FactorAvailability.ERROR, funding.availability)
        self.assertNotIn("secret", str(funding.to_dict()))

    def test_candle_failure_is_recorded_after_funding_call(self):
        service = FakeFundingService()
        result = scanner_result(
            ("BTC", "ETH"),
            service,
            FakeCandleSource(failures=("ETH",)),
        )
        self.assertIn("ETH", result.failed_assets)
        self.assertEqual(["BTC", "ETH"], service.calls)

    def test_builder_receives_available_funding_score(self):
        result = scanner_result(("BTC",))
        item = result.items[0]
        funding = item.build_result.factor_values["funding_divergence"]
        self.assertIs(FactorAvailability.AVAILABLE, funding.availability)
        self.assertEqual(
            funding.score,
            item.build_result.candidate.funding_divergence_score,
        )
        self.assertEqual(83.333333, item.build_result.candidate.data_completeness_score)

    def test_non_available_funding_state_is_preserved(self):
        service = FakeFundingService(
            results={"BTC": funding_result({"binance": venue("binance", 0.01)})}
        )
        item = scanner_result(("BTC",), service).items[0]
        funding = item.build_result.factor_values["funding_divergence"]
        self.assertIs(FactorAvailability.MISSING, funding.availability)
        self.assertEqual(0.0, item.build_result.candidate.funding_divergence_score)
        self.assertEqual(66.666667, item.build_result.candidate.data_completeness_score)

    def test_unsupported_funding_is_excluded_from_completeness(self):
        service = FakeFundingService(
            results={"BTC": funding_result(status="unsupported")}
        )
        item = scanner_result(("BTC",), service).items[0]
        self.assertEqual(80.0, item.build_result.candidate.data_completeness_score)

    def test_ranking_with_funding_is_deterministic(self):
        service = FakeFundingService(
            results={
                "BTC": funding_result(
                    {"binance": venue("binance", 0.01), "okx": venue("okx", 0.011)}
                ),
                "ETH": funding_result(
                    {"binance": venue("binance", -0.10), "okx": venue("okx", 0.10)}
                ),
            }
        )
        first = scanner_result(("BTC", "ETH"), service)
        service.calls.clear()
        second = scanner_result(("BTC", "ETH"), service)
        self.assertEqual(
            tuple(item.symbol for item in first.items),
            tuple(item.symbol for item in second.items),
        )
        self.assertEqual("ETH", first.items[0].symbol)

    def test_formatter_shows_funding_status_score_and_venues(self):
        output = format_scan_result(scanner_result(("BTC",)))
        self.assertIn("Funding: AVAILABLE", output)
        self.assertIn("Funding venues: Binance, Okx", output)
        self.assertNotIn("BUY", output)
        self.assertNotIn("SELL", output)


if __name__ == "__main__":
    unittest.main()
