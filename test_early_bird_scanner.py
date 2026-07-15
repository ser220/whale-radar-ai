"""Offline scanner, formatter, and dependency tests for PS-3 Step 1."""

import ast
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import importlib
from pathlib import Path
import unittest

from app.domain.candle import Candle
from app.intelligence.early_bird import EarlyBirdEngine, FactorAvailability
from app.intelligence.early_bird.scanner import (
    DEFAULT_ASSETS,
    EarlyBirdScanner,
    EarlyBirdScanResult,
    format_scan_result,
)


UTC = timezone.utc
NOW = datetime(2026, 7, 15, 15, 0, tzinfo=UTC)
INTERVAL = timedelta(minutes=15)


def candles(asset, count=100):
    base = 100.0 + len(asset)
    result = []
    for index in range(count):
        price = base + index * (0.01 if asset != "BTC" else 0.005)
        volume = 100.0
        if index == count - 1:
            volume = 100.0 + len(asset) * 50.0
        result.append(
            Candle(
                timestamp=NOW - INTERVAL * (count - index),
                open=price,
                high=price * 1.01,
                low=price * 0.99,
                close=price,
                volume=volume,
            )
        )
    return result


class FakeCandleSource:
    def __init__(self, failures=()):
        self.failures = set(failures)
        self.calls = []

    def source_name(self):
        return "fake-binance-public-spot"

    def get_candles(self, asset, interval, start_time, end_time=None, limit=1000):
        del start_time
        del end_time
        del limit
        normalized = asset.upper().replace("USDT", "")
        self.calls.append((normalized, interval))
        if normalized in self.failures:
            raise RuntimeError("offline fixture failure for {0}".format(normalized))
        return candles(normalized)


class FakeFundingService:
    def __init__(self):
        self.calls = []

    def build(self, asset):
        normalized = asset.upper().replace("USDT", "")
        self.calls.append(normalized)
        return {
            "status": "unavailable",
            "asset": normalized,
            "exchanges": {},
            "unavailable_exchanges": {},
            "captured_at": NOW.isoformat(),
        }


class TrackingEngine:
    def __init__(self):
        self.calls = 0
        self.delegate = EarlyBirdEngine()

    def rank_candidates(self, candidates, *, limit, timestamp):
        self.calls += 1
        return self.delegate.rank_candidates(
            candidates,
            limit=limit,
            timestamp=timestamp,
        )


def scan(
    assets=("BTC", "ETH"),
    source=None,
    engine=None,
    funding_service=None,
    **overrides
):
    scanner = EarlyBirdScanner(
        candle_source=source or FakeCandleSource(),
        funding_service=funding_service or FakeFundingService(),
        engine=engine,
    )
    arguments = {
        "timeframe": "15m",
        "candle_count": 100,
        "limit": 10,
        "timestamp": NOW,
    }
    arguments.update(overrides)
    return scanner.scan(assets, **arguments)


def runtime_imports(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


class ScannerTests(unittest.TestCase):
    def test_scanner_fetches_benchmark_once(self):
        source = FakeCandleSource()
        scan(("ETH", "SOL"), source=source)
        self.assertEqual(1, source.calls.count(("BTC", "15m")))

    def test_scanner_fetches_each_requested_asset_once(self):
        source = FakeCandleSource()
        scan(("BTC", "ETH", "SOL"), source=source)
        self.assertEqual(
            [("BTC", "15m"), ("ETH", "15m"), ("SOL", "15m")],
            source.calls,
        )

    def test_scanner_fetches_funding_once_per_requested_asset(self):
        funding_service = FakeFundingService()
        scan(
            ("BTC", "ETH", "SOL"),
            funding_service=funding_service,
        )
        self.assertEqual(["BTC", "ETH", "SOL"], funding_service.calls)

    def test_one_asset_failure_does_not_abort(self):
        result = scan(
            ("BTC", "ETH", "SOL"),
            source=FakeCandleSource(failures=("ETH",)),
        )
        self.assertIn("ETH", result.failed_assets)
        self.assertIn("BTC", result.successful_assets)
        self.assertIn("SOL", result.successful_assets)
        self.assertIn("ETH", result.errors)

    def test_total_failure_returns_explicit_result(self):
        result = scan(
            ("BTC", "ETH"),
            source=FakeCandleSource(failures=("BTC", "ETH")),
        )
        self.assertEqual((), result.items)
        self.assertEqual(("BTC", "ETH"), result.failed_assets)
        self.assertEqual(2, len(result.errors))

    def test_default_asset_universe(self):
        self.assertEqual(
            ("BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "SUI", "LINK", "NEAR", "PEPE"),
            DEFAULT_ASSETS,
        )

    def test_duplicate_assets_are_deduplicated_in_input_order(self):
        source = FakeCandleSource()
        result = scan(("eth", "ETHUSDT", "btc", "BTC"), source=source)
        self.assertEqual(("ETH", "BTC"), result.requested_assets)
        self.assertEqual(1, source.calls.count(("ETH", "15m")))
        self.assertEqual(1, source.calls.count(("BTC", "15m")))

    def test_successful_factors_are_mapped_through_candidate_builder(self):
        result = scan(("BTC",))
        item = result.items[0]
        self.assertEqual(
            (
                "volume_expansion",
                "relative_strength",
                "structure_event",
                "momentum_shift",
            ),
            item.build_result.available_factors,
        )
        self.assertGreaterEqual(item.build_result.candidate.volume_expansion_score, 0)

    def test_missing_whale_and_funding_are_explicit(self):
        values = scan(("BTC",)).items[0].build_result.factor_values
        self.assertIs(
            FactorAvailability.MISSING,
            values["whale_activity"].availability,
        )
        self.assertIs(
            FactorAvailability.MISSING,
            values["funding_divergence"].availability,
        )

    def test_unsupported_oi_and_liquidity_are_explicit(self):
        values = scan(("BTC",)).items[0].build_result.factor_values
        self.assertIs(
            FactorAvailability.UNSUPPORTED,
            values["open_interest_change"].availability,
        )
        self.assertIs(
            FactorAvailability.UNSUPPORTED,
            values["liquidity_event"].availability,
        )

    def test_completeness_is_four_of_six_supported_factors(self):
        candidate = scan(("BTC",)).items[0].build_result.candidate
        self.assertEqual(66.666667, candidate.data_completeness_score)

    def test_early_bird_engine_ranking_is_used(self):
        engine = TrackingEngine()
        result = scan(("BTC", "ETH", "SOL"), engine=engine)
        self.assertEqual(1, engine.calls)
        self.assertEqual((1, 2, 3), tuple(item.assessment.rank for item in result.items))

    def test_limit_does_not_turn_unranked_success_into_failure(self):
        result = scan(("BTC", "ETH", "SOL"), limit=1)
        self.assertEqual(1, len(result.items))
        self.assertEqual(3, len(result.successful_assets))
        self.assertEqual((), result.failed_assets)

    def test_scan_result_and_items_are_immutable(self):
        result = scan(("BTC",))
        with self.assertRaises(FrozenInstanceError):
            result.timeframe = "1h"
        with self.assertRaises(FrozenInstanceError):
            result.items[0].symbol = "ETH"

    def test_errors_are_immutable(self):
        result = scan(
            ("BTC", "ETH"),
            source=FakeCandleSource(failures=("ETH",)),
        )
        with self.assertRaises(TypeError):
            result.errors["SOL"] = "failure"

    def test_formatter_output_contains_rank_scores_and_availability(self):
        output = format_scan_result(scan(("BTC",)))
        self.assertIn("1. BTC", output)
        self.assertIn("Opportunity:", output)
        self.assertIn("Priority:", output)
        self.assertIn("Maturity:", output)
        self.assertIn("Available factors:", output)
        self.assertIn("Missing factors:", output)
        self.assertIn("Unsupported factors:", output)

    def test_formatter_lists_failed_assets(self):
        result = scan(
            ("BTC", "ETH"),
            source=FakeCandleSource(failures=("ETH",)),
        )
        output = format_scan_result(result)
        self.assertIn("Failed assets:", output)
        self.assertIn("- ETH:", output)

    def test_formatter_does_not_present_missing_whale_as_measured_absence(self):
        output = format_scan_result(scan(("BTC",)))
        self.assertNotIn("No whale activity is present", output)
        self.assertIn("whale_activity' is missing", output)

    def test_demo_script_import_is_safe(self):
        module = importlib.import_module("run_early_bird_demo")
        self.assertTrue(callable(module.main))
        self.assertTrue(callable(module.build_parser))

    def test_timestamp_and_timeframe_are_preserved(self):
        result = scan(("BTC",))
        self.assertEqual(NOW, result.started_at)
        self.assertEqual("15m", result.timeframe)
        self.assertEqual(NOW, result.items[0].scanned_at)
        self.assertIs(UTC, result.started_at.tzinfo)

    def test_invalid_scan_arguments_are_rejected(self):
        scanner = EarlyBirdScanner(candle_source=FakeCandleSource())
        with self.assertRaises(ValueError):
            scanner.scan((), timestamp=NOW)
        with self.assertRaises(ValueError):
            scanner.scan(("BTC",), candle_count=20, timestamp=NOW)
        with self.assertRaises(ValueError):
            scanner.scan(("BTC",), limit=0, timestamp=NOW)
        with self.assertRaises(ValueError):
            scanner.scan(("BTC",), timeframe="1M", timestamp=NOW)


class DependencyBoundaryTests(unittest.TestCase):
    def test_scanner_runtime_has_no_forbidden_imports(self):
        paths = (
            "app/intelligence/early_bird/scanner/candle_factors.py",
            "app/intelligence/early_bird/scanner/scanner.py",
            "app/intelligence/early_bird/scanner/formatter.py",
            "run_early_bird_demo.py",
        )
        imports = tuple(
            name.lower() for path in paths for name in runtime_imports(path)
        )
        forbidden = (
            "telegram",
            "database",
            "repository",
            "decision",
            "trade_readiness",
            "market_state",
            "expert",
            "arkham",
            "coinglass",
            "nansen",
            "requests",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertFalse(any(token in item for item in imports), imports)

    def test_only_public_binance_source_is_imported(self):
        imports = runtime_imports(
            "app/intelligence/early_bird/scanner/scanner.py"
        )
        source_imports = tuple(
            item for item in imports if item.startswith("app.sources")
        )
        self.assertEqual(
            ("app.sources.binance_candle_source",),
            source_imports,
        )

    def test_only_unified_funding_service_boundary_is_imported(self):
        imports = runtime_imports(
            "app/intelligence/early_bird/scanner/scanner.py"
        )
        service_imports = tuple(
            item for item in imports if item.startswith("app.services")
        )
        self.assertEqual(
            ("app.services.unified_funding_hub",),
            service_imports,
        )

    def test_funding_factor_has_no_provider_imports(self):
        imports = runtime_imports(
            "app/intelligence/early_bird/scanner/funding_factor.py"
        )
        application_imports = tuple(
            item for item in imports if item.startswith("app.")
        )
        self.assertEqual(
            ("app.intelligence.early_bird.availability",),
            application_imports,
        )


if __name__ == "__main__":
    unittest.main()
