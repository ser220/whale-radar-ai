"""Offline tests for PS-3 Step 1 candle-derived Early Bird factors."""

from datetime import datetime, timedelta, timezone
import unittest

from app.domain.candle import Candle
from app.intelligence.early_bird import FactorAvailability
from app.intelligence.early_bird.scanner.candle_factors import (
    CandleFactorCalculator,
)


UTC = timezone.utc
NOW = datetime(2026, 7, 15, 15, 0, tzinfo=UTC)
INTERVAL = timedelta(minutes=15)


def candles(
    count=100,
    *,
    start_price=100.0,
    end_price=100.0,
    volume=100.0,
    shift=timedelta(0),
):
    result = []
    for index in range(count):
        fraction = index / max(count - 1, 1)
        close = start_price + (end_price - start_price) * fraction
        open_price = close
        timestamp = NOW - INTERVAL * (count - index) + shift
        result.append(
            Candle(
                timestamp=timestamp,
                open=open_price,
                high=close * 1.01,
                low=close * 0.99,
                close=close,
                volume=volume,
            )
        )
    return result


def replace_candle(series, index, **overrides):
    original = series[index]
    values = {
        "timestamp": original.timestamp,
        "open": original.open,
        "high": original.high,
        "low": original.low,
        "close": original.close,
        "volume": original.volume,
    }
    values.update(overrides)
    series[index] = Candle(**values)


def factor_map(asset_candles, benchmark=None, asset="ETH"):
    values = CandleFactorCalculator().build(
        asset,
        asset_candles,
        asset_candles if benchmark is None else benchmark,
        timeframe="15m",
        evaluated_at=NOW,
    )
    return {value.factor_name: value for value in values}


class CandleFactorTests(unittest.TestCase):
    def test_volume_normal_case(self):
        value = factor_map(candles())["volume_expansion"]
        self.assertIs(FactorAvailability.AVAILABLE, value.availability)
        self.assertEqual(0.0, value.score)
        self.assertEqual(1.0, value.metadata["volume_ratio"])

    def test_volume_expansion(self):
        values = candles()
        replace_candle(values, -1, volume=400.0)
        value = factor_map(values)["volume_expansion"]
        self.assertEqual(100.0, value.score)

    def test_zero_median_volume_is_error(self):
        values = candles()
        for index in range(-21, -1):
            replace_candle(values, index, volume=0.0)
        value = factor_map(values)["volume_expansion"]
        self.assertIs(FactorAvailability.ERROR, value.availability)
        self.assertIsNone(value.score)
        self.assertIn("zero", value.reason.lower())

    def test_relative_strength_positive(self):
        asset_values = candles(start_price=100, end_price=110)
        benchmark = candles(start_price=100, end_price=100)
        value = factor_map(asset_values, benchmark)["relative_strength"]
        self.assertGreater(value.score, 50.0)
        self.assertGreater(value.metadata["excess_return_percent"], 0.0)

    def test_relative_strength_negative(self):
        asset_values = candles(start_price=100, end_price=90)
        benchmark = candles(start_price=100, end_price=100)
        value = factor_map(asset_values, benchmark)["relative_strength"]
        self.assertLess(value.score, 50.0)
        self.assertLess(value.metadata["excess_return_percent"], 0.0)

    def test_btc_self_benchmark(self):
        values = factor_map(candles(), asset="BTC")["relative_strength"]
        self.assertEqual(50.0, values.score)
        self.assertTrue(values.metadata["benchmark_self_case"])
        self.assertEqual(0.0, values.metadata["excess_return_percent"])

    def test_timestamp_misalignment_is_error(self):
        asset_values = candles()
        benchmark = candles(shift=timedelta(minutes=1))
        value = factor_map(asset_values, benchmark)["relative_strength"]
        self.assertIs(FactorAvailability.ERROR, value.availability)
        self.assertIsNone(value.score)

    def test_structure_breakout(self):
        values = candles()
        replace_candle(
            values,
            -1,
            open=105,
            high=106,
            low=104,
            close=105,
        )
        value = factor_map(values)["structure_event"]
        self.assertGreaterEqual(value.score, 60.0)
        self.assertEqual("UP", value.metadata["structure_direction"])

    def test_structure_breakdown(self):
        values = candles()
        replace_candle(
            values,
            -1,
            open=95,
            high=96,
            low=94,
            close=95,
        )
        value = factor_map(values)["structure_event"]
        self.assertGreaterEqual(value.score, 60.0)
        self.assertEqual("DOWN", value.metadata["structure_direction"])

    def test_structure_inside_range(self):
        value = factor_map(candles())["structure_event"]
        self.assertLessEqual(value.score, 50.0)
        self.assertEqual("INSIDE", value.metadata["structure_direction"])

    def test_structure_score_has_no_directional_sign(self):
        up = candles()
        down = candles()
        replace_candle(up, -1, open=105, high=106, low=104, close=105)
        replace_candle(down, -1, open=95, high=96, low=94, close=95)
        up_value = factor_map(up)["structure_event"]
        down_value = factor_map(down)["structure_event"]
        self.assertGreaterEqual(up_value.score, 0.0)
        self.assertGreaterEqual(down_value.score, 0.0)
        self.assertEqual("METADATA_ONLY", up_value.metadata["direction_semantics"])
        self.assertEqual(
            "METADATA_ONLY",
            down_value.metadata["direction_semantics"],
        )

    def test_momentum_acceleration(self):
        values = candles()
        for index in range(-3, 0):
            replace_candle(
                values,
                index,
                open=100,
                high=103,
                low=99,
                close=102,
            )
        value = factor_map(values)["momentum_shift"]
        self.assertEqual(100.0, value.score)
        self.assertEqual("UP", value.metadata["momentum_direction"])

    def test_momentum_deceleration_uses_absolute_magnitude(self):
        values = candles()
        for index in range(-3, 0):
            replace_candle(
                values,
                index,
                open=100,
                high=101,
                low=97,
                close=98,
            )
        value = factor_map(values)["momentum_shift"]
        self.assertEqual(100.0, value.score)
        self.assertEqual("DOWN", value.metadata["momentum_direction"])

    def test_insufficient_candles_create_explicit_errors(self):
        values = factor_map(candles(count=10))
        self.assertTrue(
            all(
                value.availability is FactorAvailability.ERROR
                for value in values.values()
            )
        )

    def test_irregular_timestamps_reduce_quality(self):
        regular = candles()
        irregular = candles()
        replace_candle(
            irregular,
            50,
            timestamp=irregular[50].timestamp + timedelta(minutes=2),
        )
        regular_quality = factor_map(regular)["volume_expansion"].quality
        irregular_quality = factor_map(irregular)["volume_expansion"].quality
        self.assertLess(irregular_quality, regular_quality)

    def test_malformed_input_reduces_quality_without_becoming_a_score(self):
        clean = candles()
        malformed = list(clean) + [object()]
        clean_quality = factor_map(clean)["volume_expansion"].quality
        malformed_quality = factor_map(malformed)["volume_expansion"].quality
        self.assertLess(malformed_quality, clean_quality)

    def test_factor_timestamp_is_latest_completed_candle_close(self):
        values = factor_map(candles())
        self.assertTrue(
            all(value.observed_at == NOW for value in values.values())
        )

    def test_forming_candle_is_excluded(self):
        values = candles()
        forming = Candle(
            timestamp=NOW,
            open=100,
            high=500,
            low=99,
            close=400,
            volume=10000,
        )
        values.append(forming)
        result = factor_map(values)
        self.assertEqual(0.0, result["volume_expansion"].score)
        self.assertEqual(NOW, result["volume_expansion"].observed_at)


if __name__ == "__main__":
    unittest.main()
