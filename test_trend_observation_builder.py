import ast
import json
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.intelligence.builders import (
    Candle,
    TrendObservationBuilder,
    TrendObservationBuilderPolicy,
)
from app.intelligence.contracts import ExpertOpinion
from app.intelligence.experts.trend import TrendExpert
from app.intelligence.market_state import MarketStateEngine
from app.intelligence.observations import (
    StructureBreak,
    StructureObservation,
    TrendBias,
    TrendObservation,
)


START = datetime(2026, 7, 13, 0, 0, tzinfo=timezone.utc)


def candle(index=0, close=100.0, *, volume=10.0, open_time=None):
    timestamp = open_time or START + timedelta(hours=index)
    return Candle(
        open_time=timestamp,
        open=close,
        high=close + 0.4,
        low=close - 0.4,
        close=close,
        volume=volume,
        close_time=timestamp + timedelta(minutes=59),
    )


def series(count=25, start=100.0, step=1.0, *, volume=10.0):
    return [candle(index, start + step * index, volume=volume) for index in range(count)]


def range_series(count=25, *, volume=10.0):
    return [
        candle(index, 100.0 + (0.01 if index % 2 else -0.01), volume=volume)
        for index in range(count)
    ]


def build(values, **kwargs):
    inputs = {
        "asset": "btc",
        "source": "unit-test",
        "timeframe": "1h",
    }
    inputs.update(kwargs)
    return TrendObservationBuilder().build(values, **inputs)


class CandleContractTests(unittest.TestCase):
    def test_valid_candle_creation(self):
        value = candle()
        self.assertEqual(value.close, 100.0)
        self.assertEqual(value.volume, 10.0)

    def test_candle_is_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            candle().close = 101

    def test_timestamps_are_normalized_to_utc(self):
        offset = timezone(timedelta(hours=2))
        value = candle(open_time=datetime(2026, 7, 13, 2, 0, tzinfo=offset))
        self.assertEqual(value.open_time, START)
        self.assertIs(value.open_time.tzinfo, timezone.utc)

    def test_naive_open_time_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            candle(open_time=datetime(2026, 7, 13))

    def test_naive_close_time_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            Candle(START, 100, 101, 99, 100, 1, datetime(2026, 7, 13, 1))

    def test_low_above_open_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "low"):
            Candle(START, 100, 101, 100.1, 101, 1)

    def test_high_below_close_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "high"):
            Candle(START, 100, 100.5, 99, 101, 1)

    def test_non_positive_ohlc_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "greater than 0"):
            Candle(START, 0, 101, 0, 100, 1)

    def test_negative_volume_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "greater than or equal to 0"):
            Candle(START, 100, 101, 99, 100, -1)

    def test_close_time_before_open_time_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "earlier"):
            Candle(START, 100, 101, 99, 100, 1, START - timedelta(seconds=1))

    def test_serialization_round_trip(self):
        value = candle()
        restored = Candle.from_dict(value.to_dict())
        self.assertEqual(restored, value)
        json.dumps(restored.to_dict())

    def test_from_dict_accepts_datetime(self):
        payload = candle().to_dict()
        payload["open_time"] = START
        self.assertEqual(Candle.from_dict(payload).open_time, START)

    def test_boolean_ohlc_is_rejected(self):
        with self.assertRaises(TypeError):
            Candle(START, True, 101, 99, 100, 1)

    def test_boolean_volume_is_rejected(self):
        with self.assertRaises(TypeError):
            Candle(START, 100, 101, 99, 100, False)

    def test_non_finite_numbers_are_rejected(self):
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Candle(START, 100, 101, 99, value, 1)


class BuilderPolicyTests(unittest.TestCase):
    def test_default_policy_is_explicit(self):
        policy = TrendObservationBuilderPolicy()
        self.assertEqual(policy.minimum_candles, 20)
        self.assertEqual(policy.short_window, 5)
        self.assertEqual(policy.long_window, 20)
        self.assertEqual(policy.slope_window, 10)
        self.assertEqual(policy.swing_lookback, 5)
        self.assertEqual(policy.range_lookback, 20)
        self.assertEqual(policy.observation_version, 1)

    def test_builder_exposes_policy(self):
        policy = TrendObservationBuilderPolicy(policy_version="custom")
        self.assertIs(TrendObservationBuilder(policy).policy, policy)

    def test_invalid_policy_type_is_rejected(self):
        with self.assertRaises(TypeError):
            TrendObservationBuilder(object())

    def test_boolean_window_is_rejected(self):
        with self.assertRaises(TypeError):
            TrendObservationBuilderPolicy(short_window=True)

    def test_windows_must_be_at_least_two(self):
        with self.assertRaises(ValueError):
            TrendObservationBuilderPolicy(short_window=1)

    def test_long_window_must_cover_short_window(self):
        with self.assertRaises(ValueError):
            TrendObservationBuilderPolicy(short_window=10, long_window=5)

    def test_minimum_must_cover_long_window(self):
        with self.assertRaises(ValueError):
            TrendObservationBuilderPolicy(minimum_candles=10)

    def test_minimum_must_cover_two_swing_blocks(self):
        with self.assertRaises(ValueError):
            TrendObservationBuilderPolicy(swing_lookback=11)

    def test_only_v1_is_supported(self):
        with self.assertRaisesRegex(ValueError, "version 1"):
            TrendObservationBuilderPolicy(observation_version=2)

    def test_weak_threshold_must_not_exceed_strong(self):
        with self.assertRaises(ValueError):
            TrendObservationBuilderPolicy(
                weak_trend_threshold=80, strong_trend_threshold=70
            )


class BuilderValidationTests(unittest.TestCase):
    def test_empty_candles_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            build([])

    def test_insufficient_candles_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least 20"):
            build(series(19))

    def test_invalid_candle_type_is_rejected(self):
        values = series(20)
        values[-1] = object()
        with self.assertRaisesRegex(TypeError, "Candle"):
            build(values)

    def test_duplicate_timestamp_is_rejected(self):
        values = series(20)
        values[-1] = replace(values[-1], open_time=values[-2].open_time)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build(values)

    def test_out_of_order_timestamp_is_rejected(self):
        values = series(20)
        values[-1] = replace(
            values[-1], open_time=values[-2].open_time - timedelta(minutes=1)
        )
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            build(values)

    def test_asset_is_required_and_normalized(self):
        trend, structure = build(series(), asset="  btc  ")
        self.assertEqual(trend.asset, "BTC")
        self.assertEqual(structure.asset, "BTC")
        with self.assertRaises(ValueError):
            build(series(), asset=" ")

    def test_source_is_required(self):
        with self.assertRaises(ValueError):
            build(series(), source="")

    def test_timeframe_is_required(self):
        with self.assertRaises(ValueError):
            build(series(), timeframe="")

    def test_input_candles_are_unchanged(self):
        values = series()
        before = [item.to_dict() for item in values]
        build(values)
        self.assertEqual([item.to_dict() for item in values], before)

    def test_tuple_and_generator_are_accepted(self):
        values = series()
        self.assertIsInstance(build(tuple(values))[0], TrendObservation)
        self.assertIsInstance(build((item for item in values))[1], StructureObservation)

    def test_deterministic_distinct_observation_ids(self):
        first = build(series())
        second = build(series())
        self.assertEqual(first[0].observation_id, second[0].observation_id)
        self.assertEqual(first[1].observation_id, second[1].observation_id)
        self.assertNotEqual(first[0].observation_id, first[1].observation_id)
        self.assertEqual(
            first[0].observation_id,
            "BTC:1h:trend:v1:2026-07-14T00:00:00+00:00",
        )

    def test_custom_prefix_is_deterministic(self):
        trend, structure = build(series(), observation_id_prefix="feed:btc")
        self.assertTrue(trend.observation_id.startswith("feed:btc:trend:v1:"))
        self.assertTrue(structure.observation_id.startswith("feed:btc:structure:v1:"))

    def test_outputs_are_version_one(self):
        trend, structure = build(series())
        self.assertEqual((trend.version, structure.version), (1, 1))

    def test_latest_open_time_is_observed_at(self):
        values = series()
        trend, structure = build(values)
        self.assertEqual(trend.observed_at, values[-1].open_time)
        self.assertEqual(structure.observed_at, values[-1].open_time)


class BuilderCalculationTests(unittest.TestCase):
    def test_bullish_series_facts(self):
        trend, structure = build(series(step=1.0))
        self.assertEqual(trend.trend_bias, TrendBias.BULLISH)
        self.assertEqual(trend.moving_average_alignment, TrendBias.BULLISH)
        self.assertGreater(trend.slope, 0)
        self.assertTrue(trend.higher_high)
        self.assertTrue(trend.higher_low)
        self.assertGreater(trend.trend_strength, 0)
        self.assertIsInstance(trend, TrendObservation)
        self.assertIsInstance(structure, StructureObservation)

    def test_bearish_series_facts(self):
        trend, structure = build(series(start=150, step=-1.0))
        self.assertEqual(trend.trend_bias, TrendBias.BEARISH)
        self.assertEqual(trend.moving_average_alignment, TrendBias.BEARISH)
        self.assertLess(trend.slope, 0)
        self.assertTrue(trend.lower_high)
        self.assertTrue(trend.lower_low)
        self.assertIsInstance(structure, StructureObservation)

    def test_range_series_is_neutral_without_false_break(self):
        trend, structure = build(range_series())
        self.assertEqual(trend.trend_bias, TrendBias.NEUTRAL)
        self.assertEqual(trend.moving_average_alignment, TrendBias.NEUTRAL)
        self.assertLess(abs(trend.slope), 0.05)
        self.assertEqual(structure.structure_break, StructureBreak.NONE)
        self.assertAlmostEqual(structure.range_high, 100.41)
        self.assertAlmostEqual(structure.range_low, 99.59)

    def test_price_change_uses_latest_long_window(self):
        values = [candle(index, 50 if index < 5 else 100 + index) for index in range(25)]
        trend, _ = build(values)
        expected = 100.0 * (124.0 - 105.0) / 105.0
        self.assertAlmostEqual(trend.price_change_pct, expected)
        self.assertEqual(trend.metadata["calculation_window"], 20)

    def test_normalized_slope_is_percent_per_candle(self):
        trend, _ = build(series(start=100, step=1))
        self.assertGreater(trend.slope, 0.8)
        self.assertLess(trend.slope, 1.1)

    def test_distance_from_inclusive_range_is_zero(self):
        trend, _ = build(series())
        self.assertEqual(trend.distance_from_range_pct, 0.0)

    def test_bullish_bos(self):
        _, structure = build(series(step=1.0))
        self.assertEqual(structure.structure_break, StructureBreak.BULLISH_BOS)

    def test_bearish_bos(self):
        _, structure = build(series(start=150, step=-1.0))
        self.assertEqual(structure.structure_break, StructureBreak.BEARISH_BOS)

    def test_bullish_choch_against_prior_bearish_evidence(self):
        values = series(24, start=140, step=-1)
        values.append(candle(24, 150))
        _, structure = build(values)
        self.assertEqual(structure.structure_break, StructureBreak.BULLISH_CHOCH)

    def test_bearish_choch_against_prior_bullish_evidence(self):
        values = series(24, start=100, step=1)
        values.append(candle(24, 80))
        _, structure = build(values)
        self.assertEqual(structure.structure_break, StructureBreak.BEARISH_CHOCH)

    def test_break_has_single_classification(self):
        values = series(24, start=140, step=-1)
        values.append(candle(24, 150))
        _, structure = build(values)
        self.assertIn(structure.structure_break, tuple(StructureBreak))
        self.assertNotEqual(structure.structure_break, StructureBreak.BULLISH_BOS)

    def test_tolerance_prevents_false_break(self):
        values = range_series(24)
        previous_high = max(item.high for item in values)
        values.append(candle(24, previous_high * 1.0005))
        _, structure = build(values)
        self.assertEqual(structure.structure_break, StructureBreak.NONE)

    def test_reference_range_excludes_latest_candle(self):
        values = range_series(24)
        values.append(candle(24, 150))
        _, structure = build(values)
        self.assertLess(
            structure.metadata["reference_range_high"], structure.range_high
        )

    def test_higher_timeframe_bias_is_explicitly_unavailable(self):
        _, structure = build(series())
        self.assertEqual(structure.higher_timeframe_bias, TrendBias.NEUTRAL)
        self.assertIs(
            structure.metadata["higher_timeframe_bias_available"], False
        )


class BuilderQualityAndMetadataTests(unittest.TestCase):
    def test_regular_timestamps_have_higher_quality_than_irregular(self):
        regular = series()
        irregular = []
        timestamp = START
        for index in range(25):
            irregular.append(candle(index, 100 + index, open_time=timestamp))
            timestamp += timedelta(hours=2 if index % 3 == 0 else 1)
        regular_trend, _ = build(regular)
        irregular_trend, _ = build(irregular)
        self.assertGreater(regular_trend.quality, irregular_trend.quality)

    def test_zero_volume_reduces_quality(self):
        normal, _ = build(series(volume=10))
        zero, _ = build(series(volume=0))
        self.assertGreater(normal.quality, zero.quality)

    def test_additional_coverage_improves_or_preserves_quality(self):
        minimum, _ = build(series(20))
        additional, _ = build(series(30))
        self.assertGreaterEqual(additional.quality, minimum.quality)

    def test_all_quality_values_are_bounded(self):
        for values in (series(), range_series(), series(volume=0)):
            trend, structure = build(values)
            for value in (trend.quality, structure.quality, structure.structure_quality):
                self.assertGreaterEqual(value, 0.0)
                self.assertLessEqual(value, 100.0)

    def test_required_metadata_keys_are_present(self):
        trend, _ = build(series())
        required = {
            "candle_count",
            "first_open_time",
            "latest_open_time",
            "median_interval_seconds",
            "irregular_interval_ratio",
            "short_sma",
            "long_sma",
            "reference_range_high",
            "reference_range_low",
            "builder_policy_version",
            "calculation_window",
        }
        self.assertTrue(required.issubset(trend.metadata))

    def test_metadata_does_not_store_raw_candles(self):
        trend, structure = build(series())
        self.assertNotIn("candles", trend.metadata)
        self.assertNotIn("candles", structure.metadata)
        self.assertFalse(any(isinstance(value, Candle) for value in trend.metadata.values()))

    def test_serialized_metadata_is_json_serializable(self):
        trend, structure = build(series())
        json.dumps(trend.to_dict())
        json.dumps(structure.to_dict())

    def test_same_input_produces_equal_serialized_output(self):
        first = build(series())
        second = build(series())
        self.assertEqual(first[0].to_dict(), second[0].to_dict())
        self.assertEqual(first[1].to_dict(), second[1].to_dict())


class BuilderIntegrationAndBoundaryTests(unittest.TestCase):
    def test_trend_expert_accepts_builder_outputs(self):
        trend, structure = build(series())
        opinion = TrendExpert().evaluate(
            trend, structure, timestamp=trend.observed_at
        )
        self.assertIsInstance(opinion, ExpertOpinion)

    def test_market_state_engine_accepts_resulting_opinion(self):
        trend, structure = build(series())
        opinion = TrendExpert().evaluate(
            trend, structure, timestamp=trend.observed_at
        )
        state = MarketStateEngine().synthesize(
            [opinion], timestamp=trend.observed_at
        )
        self.assertEqual(state.timestamp, trend.observed_at)

    def test_builder_modules_respect_dependency_boundary(self):
        root = Path("app/intelligence/builders")
        forbidden = {
            "telegram",
            "fastapi",
            "database",
            "repositories",
            "persistence",
            "pipeline",
            "arkham",
            "funding",
            "exchange",
            "requests",
            "httpx",
            "pandas",
            "numpy",
            "talib",
            "experts",
            "market_state",
        }
        for path in root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name.lower() for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.append((node.module or "").lower())
            for imported in imports:
                with self.subTest(path=path, imported=imported):
                    self.assertFalse(any(name in imported for name in forbidden))


if __name__ == "__main__":
    unittest.main()
