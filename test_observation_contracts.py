import ast
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.intelligence.observations import (
    DataTrend,
    FundingBias,
    FundingObservation,
    LiquidityObservation,
    LiquiditySide,
    MomentumObservation,
    Observation,
    OpenInterestObservation,
    StructureBreak,
    StructureObservation,
    TrendBias,
    TrendObservation,
)


FIXED_TIME = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


def common(**overrides):
    values = {
        "observation_id": "obs-001",
        "asset": "btc",
        "source": "normalized-test",
        "timeframe": "4h",
        "quality": 90,
        "observed_at": FIXED_TIME,
        "metadata": {"venues": ["A", "B"], "nested": {"samples": [1, 2]}},
    }
    values.update(overrides)
    return values


def trend(**overrides):
    values = common()
    values.update(
        {
            "price_change_pct": 3.5,
            "higher_high": True,
            "higher_low": True,
            "lower_high": False,
            "lower_low": False,
            "trend_bias": TrendBias.BULLISH,
            "trend_strength": 82,
            "distance_from_range_pct": 1.4,
            "moving_average_alignment": TrendBias.BULLISH,
            "slope": 0.42,
        }
    )
    values.update(overrides)
    return TrendObservation(**values)


def momentum(**overrides):
    values = common(observation_id="momentum-001")
    values.update(
        {
            "momentum_score": 73,
            "momentum_trend": DataTrend.RISING,
            "acceleration_score": 21,
        }
    )
    values.update(overrides)
    return MomentumObservation(**values)


def structure(**overrides):
    values = common(observation_id="structure-001")
    values.update(
        {
            "structure_break": StructureBreak.BULLISH_BOS,
            "higher_timeframe_bias": TrendBias.BULLISH,
            "structure_quality": 86,
            "swing_high": 110,
            "swing_low": 90,
            "range_high": 108,
            "range_low": 92,
            "current_price": 105,
        }
    )
    values.update(overrides)
    return StructureObservation(**values)


def funding(**overrides):
    values = common(observation_id="funding-001", timeframe="8h")
    values.update(
        {
            "funding_rate": 0.0003,
            "funding_bias": FundingBias.LONG_CROWDED,
            "funding_trend": DataTrend.RISING,
            "exchange_count": 4,
            "annualized_funding_pct": 32.85,
            "spread_pct": 0.012,
        }
    )
    values.update(overrides)
    return FundingObservation(**values)


def open_interest(**overrides):
    values = common(observation_id="oi-001")
    values.update(
        {
            "open_interest": 1_500_000,
            "open_interest_change_pct": 4.2,
            "oi_trend": DataTrend.RISING,
            "price_change_pct": 2.1,
            "leverage_concentration": 64,
            "exchange_count": 5,
        }
    )
    values.update(overrides)
    return OpenInterestObservation(**values)


def liquidity(**overrides):
    values = common(observation_id="liquidity-001")
    values.update(
        {
            "nearest_liquidity_side": LiquiditySide.BUY_SIDE,
            "buy_side_liquidity_usd": 2_000_000,
            "sell_side_liquidity_usd": 1_200_000,
            "distance_to_buy_side_pct": 1.5,
            "distance_to_sell_side_pct": 3.1,
            "liquidity_imbalance": 25,
            "liquidity_quality": 89,
        }
    )
    values.update(overrides)
    return LiquidityObservation(**values)


class CommonObservationTests(unittest.TestCase):
    def test_shared_enum_values_match_contract(self):
        self.assertEqual(
            [value.value for value in StructureBreak],
            [
                "NONE",
                "BULLISH_BOS",
                "BEARISH_BOS",
                "BULLISH_CHOCH",
                "BEARISH_CHOCH",
            ],
        )
        self.assertEqual(
            [value.value for value in TrendBias],
            ["BULLISH", "BEARISH", "NEUTRAL"],
        )
        self.assertEqual(
            [value.value for value in FundingBias],
            ["LONG_CROWDED", "SHORT_CROWDED", "BALANCED", "UNKNOWN"],
        )
        self.assertEqual(
            [value.value for value in LiquiditySide],
            ["BUY_SIDE", "SELL_SIDE", "BOTH", "NONE"],
        )
        self.assertEqual(
            [value.value for value in DataTrend],
            ["RISING", "FALLING", "STABLE", "UNKNOWN"],
        )

    def test_common_base_is_abstract(self):
        with self.assertRaises(TypeError):
            Observation()

    def test_model_is_immutable(self):
        value = trend()
        with self.assertRaises(FrozenInstanceError):
            value.asset = "ETH"

    def test_asset_is_trimmed_and_uppercase(self):
        self.assertEqual(trend(asset="  eth  ").asset, "ETH")

    def test_empty_common_text_is_rejected(self):
        for field_name in ("observation_id", "asset", "source", "timeframe"):
            with self.subTest(field_name=field_name):
                with self.assertRaises(ValueError):
                    trend(**{field_name: "   "})

    def test_common_text_requires_strings(self):
        with self.assertRaises(TypeError):
            trend(source=123)

    def test_version_defaults_to_one_and_rejects_lower_values(self):
        self.assertEqual(trend().version, 1)
        with self.assertRaises(ValueError):
            trend(version=0)

    def test_version_rejects_boolean(self):
        with self.assertRaises(TypeError):
            trend(version=True)

    def test_quality_accepts_boundaries(self):
        self.assertEqual(trend(quality=0).quality, 0.0)
        self.assertEqual(trend(quality=100).quality, 100.0)

    def test_quality_rejects_out_of_range(self):
        for invalid in (-0.1, 100.1):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    trend(quality=invalid)

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            trend(observed_at=datetime(2026, 7, 14, 12, 0))

    def test_aware_timestamp_is_normalized_to_utc(self):
        supplied = datetime(2026, 7, 14, 14, 0, tzinfo=timezone(timedelta(hours=2)))
        value = trend(observed_at=supplied)
        self.assertEqual(value.observed_at, FIXED_TIME)
        self.assertIs(value.observed_at.tzinfo, timezone.utc)

    def test_metadata_is_defensively_frozen(self):
        original = {"levels": [1, 2], "nested": {"active": [True]}}
        value = trend(metadata=original)
        original["levels"].append(3)
        original["nested"]["active"].append(False)

        self.assertEqual(value.metadata["levels"], (1, 2))
        self.assertEqual(value.metadata["nested"]["active"], (True,))
        with self.assertRaises(TypeError):
            value.metadata["new"] = "value"

    def test_all_observations_round_trip(self):
        values = [trend(), momentum(), structure(), funding(), open_interest(), liquidity()]
        for value in values:
            with self.subTest(observation_type=value.OBSERVATION_TYPE):
                restored = type(value).from_dict(value.to_dict())
                self.assertEqual(restored, value)
                self.assertEqual(restored.version, value.version)
                self.assertIs(restored.observed_at.tzinfo, timezone.utc)

    def test_serialization_uses_public_primitives(self):
        payload = trend(version=3).to_dict()
        self.assertEqual(payload["observation_type"], "trend")
        self.assertEqual(payload["trend_bias"], "BULLISH")
        self.assertEqual(payload["version"], 3)
        self.assertIsInstance(payload["observed_at"], str)
        self.assertIsInstance(payload["metadata"], dict)
        self.assertIsInstance(payload["metadata"]["venues"], list)

    def test_wrong_serialized_observation_type_is_rejected(self):
        payload = trend().to_dict()
        payload["observation_type"] = "funding"
        with self.assertRaises(ValueError):
            TrendObservation.from_dict(payload)

    def test_booleans_are_rejected_as_numerics(self):
        cases = (
            lambda: trend(quality=True),
            lambda: momentum(momentum_score=True),
            lambda: funding(funding_rate=False),
            lambda: open_interest(exchange_count=True),
        )
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    case()

    def test_nan_and_infinity_are_rejected(self):
        for invalid in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    trend(price_change_pct=invalid)


class TrendObservationTests(unittest.TestCase):
    def test_valid_creation(self):
        value = trend()
        self.assertEqual(value.asset, "BTC")
        self.assertEqual(value.trend_bias, TrendBias.BULLISH)

    def test_strength_boundaries(self):
        self.assertEqual(trend(trend_strength=0).trend_strength, 0.0)
        self.assertEqual(trend(trend_strength=100).trend_strength, 100.0)
        for invalid in (-1, 101):
            with self.assertRaises(ValueError):
                trend(trend_strength=invalid)

    def test_contradictory_flags_are_accepted(self):
        value = trend(higher_high=True, higher_low=True, lower_high=True, lower_low=True)
        self.assertTrue(value.higher_high and value.lower_high)

    def test_enum_round_trip(self):
        restored = TrendObservation.from_dict(trend().to_dict())
        self.assertIs(restored.trend_bias, TrendBias.BULLISH)
        self.assertIs(restored.moving_average_alignment, TrendBias.BULLISH)

    def test_structure_flags_require_booleans(self):
        with self.assertRaises(TypeError):
            trend(higher_high=1)


class MomentumObservationTests(unittest.TestCase):
    def test_valid_optional_values(self):
        value = momentum(rsi=67.2, macd_histogram=-0.3, volume_change_pct=18.0)
        self.assertEqual(value.rsi, 67.2)
        self.assertEqual(value.macd_histogram, -0.3)

    def test_optional_values_may_be_none(self):
        value = momentum()
        self.assertIsNone(value.rsi)
        self.assertIsNone(value.macd_histogram)

    def test_rsi_boundaries(self):
        self.assertEqual(momentum(rsi=0).rsi, 0.0)
        self.assertEqual(momentum(rsi=100).rsi, 100.0)
        for invalid in (-1, 101):
            with self.assertRaises(ValueError):
                momentum(rsi=invalid)

    def test_acceleration_boundaries(self):
        self.assertEqual(momentum(acceleration_score=-100).acceleration_score, -100.0)
        self.assertEqual(momentum(acceleration_score=100).acceleration_score, 100.0)
        for invalid in (-101, 101):
            with self.assertRaises(ValueError):
                momentum(acceleration_score=invalid)


class StructureObservationTests(unittest.TestCase):
    def test_valid_structure(self):
        value = structure()
        self.assertEqual(value.structure_break, StructureBreak.BULLISH_BOS)
        self.assertEqual(value.current_price, 105.0)

    def test_invalid_range_ordering_is_rejected(self):
        with self.assertRaises(ValueError):
            structure(range_low=110, range_high=100)

    def test_invalid_swing_ordering_is_rejected(self):
        with self.assertRaises(ValueError):
            structure(swing_low=110, swing_high=100)

    def test_non_positive_supplied_prices_are_rejected(self):
        for field_name in (
            "swing_high",
            "swing_low",
            "range_high",
            "range_low",
            "current_price",
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaises(ValueError):
                    structure(**{field_name: 0})

    def test_optional_prices_may_be_none(self):
        value = structure(
            swing_high=None,
            swing_low=None,
            range_high=None,
            range_low=None,
            current_price=None,
        )
        self.assertIsNone(value.current_price)


class FundingObservationTests(unittest.TestCase):
    def test_valid_positive_and_negative_funding(self):
        self.assertEqual(funding(funding_rate=0.001).funding_rate, 0.001)
        self.assertEqual(funding(funding_rate=-0.001).funding_rate, -0.001)

    def test_negative_exchange_count_is_rejected(self):
        with self.assertRaises(ValueError):
            funding(exchange_count=-1)

    def test_negative_spread_is_rejected(self):
        with self.assertRaises(ValueError):
            funding(spread_pct=-0.01)

    def test_optional_annualized_funding_must_be_finite(self):
        with self.assertRaises(ValueError):
            funding(annualized_funding_pct=float("inf"))


class OpenInterestObservationTests(unittest.TestCase):
    def test_valid_creation(self):
        value = open_interest()
        self.assertEqual(value.open_interest, 1_500_000.0)
        self.assertIs(value.oi_trend, DataTrend.RISING)

    def test_negative_open_interest_is_rejected(self):
        with self.assertRaises(ValueError):
            open_interest(open_interest=-1)

    def test_leverage_concentration_boundaries(self):
        self.assertEqual(open_interest(leverage_concentration=0).leverage_concentration, 0.0)
        self.assertEqual(open_interest(leverage_concentration=100).leverage_concentration, 100.0)
        for invalid in (-1, 101):
            with self.assertRaises(ValueError):
                open_interest(leverage_concentration=invalid)

    def test_no_derived_positioning_semantics_are_present(self):
        value = open_interest()
        for attribute in (
            "new_longs",
            "new_shorts",
            "liquidation_probability",
            "continuation_probability",
            "reversal_probability",
        ):
            self.assertFalse(hasattr(value, attribute))


class LiquidityObservationTests(unittest.TestCase):
    def test_valid_creation(self):
        value = liquidity()
        self.assertEqual(value.nearest_liquidity_side, LiquiditySide.BUY_SIDE)
        self.assertEqual(value.buy_side_liquidity_usd, 2_000_000.0)

    def test_negative_liquidity_is_rejected(self):
        for field_name in ("buy_side_liquidity_usd", "sell_side_liquidity_usd"):
            with self.subTest(field_name=field_name):
                with self.assertRaises(ValueError):
                    liquidity(**{field_name: -1})

    def test_distance_validation(self):
        for field_name in ("distance_to_buy_side_pct", "distance_to_sell_side_pct"):
            with self.subTest(field_name=field_name):
                with self.assertRaises(ValueError):
                    liquidity(**{field_name: -0.1})

    def test_imbalance_boundaries(self):
        self.assertEqual(liquidity(liquidity_imbalance=-100).liquidity_imbalance, -100.0)
        self.assertEqual(liquidity(liquidity_imbalance=100).liquidity_imbalance, 100.0)
        for invalid in (-101, 101):
            with self.assertRaises(ValueError):
                liquidity(liquidity_imbalance=invalid)

    def test_quality_boundaries(self):
        self.assertEqual(liquidity(liquidity_quality=0).liquidity_quality, 0.0)
        self.assertEqual(liquidity(liquidity_quality=100).liquidity_quality, 100.0)
        for invalid in (-1, 101):
            with self.assertRaises(ValueError):
                liquidity(liquidity_quality=invalid)


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_observation_package_has_only_allowed_import_roots(self):
        package = Path("app/intelligence/observations")
        allowed_roots = {
            "abc",
            "app.intelligence.observations",
            "collections",
            "dataclasses",
            "datetime",
            "enum",
            "math",
            "numbers",
            "types",
            "typing",
        }

        for path in package.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    imported = [node.module or ""]
                else:
                    continue
                for module in imported:
                    self.assertTrue(
                        any(module == root or module.startswith(root + ".") for root in allowed_roots),
                        msg=f"forbidden import {module!r} in {path}",
                    )


if __name__ == "__main__":
    unittest.main()
