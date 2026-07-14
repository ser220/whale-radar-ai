import ast
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.intelligence.contracts import Direction, ExpertOpinion, TrendState
from app.intelligence.experts.trend import TrendExpert, TrendExpertPolicy
from app.intelligence.market_state import MarketStateEngine
from app.intelligence.observations import (
    StructureBreak,
    StructureObservation,
    TrendBias,
    TrendObservation,
)


OBSERVED_AT = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
OUTPUT_AT = datetime(2026, 7, 14, 12, 5, tzinfo=timezone.utc)


def trend_observation(**overrides):
    values = {
        "observation_id": "trend-btc-4h-001",
        "asset": "BTC",
        "source": "test-builder",
        "timeframe": "4h",
        "quality": 90,
        "observed_at": OBSERVED_AT,
        "price_change_pct": 5,
        "higher_high": True,
        "higher_low": True,
        "lower_high": False,
        "lower_low": False,
        "trend_bias": TrendBias.BULLISH,
        "trend_strength": 80,
        "distance_from_range_pct": 2,
        "moving_average_alignment": TrendBias.BULLISH,
        "slope": 1,
    }
    values.update(overrides)
    return TrendObservation(**values)


def structure_observation(**overrides):
    values = {
        "observation_id": "structure-btc-4h-001",
        "asset": "BTC",
        "source": "test-builder",
        "timeframe": "4h",
        "quality": 90,
        "observed_at": OBSERVED_AT,
        "structure_break": StructureBreak.BULLISH_BOS,
        "higher_timeframe_bias": TrendBias.BULLISH,
        "structure_quality": 88,
        "swing_high": 110,
        "swing_low": 90,
        "range_high": 108,
        "range_low": 92,
        "current_price": 105,
    }
    values.update(overrides)
    return StructureObservation(**values)


def evaluate(trend=None, structure=None, expert=None, timestamp=OUTPUT_AT):
    return (expert or TrendExpert()).evaluate(
        trend or trend_observation(),
        structure or structure_observation(),
        timestamp=timestamp,
    )


class TrendExpertPublicBehaviorTests(unittest.TestCase):
    def test_name_and_default_policy(self):
        expert = TrendExpert()
        self.assertEqual(expert.name, "trend")
        self.assertEqual(expert.policy.supported_versions, (1,))

    def test_valid_bullish_trend(self):
        opinion = evaluate()
        self.assertEqual(opinion.direction, Direction.BULLISH)
        self.assertEqual(opinion.state, TrendState.TREND.value)

    def test_valid_bearish_trend(self):
        trend = trend_observation(
            price_change_pct=-5,
            higher_high=False,
            higher_low=False,
            lower_high=True,
            lower_low=True,
            trend_bias=TrendBias.BEARISH,
            moving_average_alignment=TrendBias.BEARISH,
            slope=-1,
        )
        structure = structure_observation(
            structure_break=StructureBreak.BEARISH_BOS,
            higher_timeframe_bias=TrendBias.BEARISH,
        )

        opinion = evaluate(trend, structure)

        self.assertEqual(opinion.direction, Direction.BEARISH)
        self.assertEqual(opinion.state, TrendState.TREND.value)

    def test_neutral_range(self):
        trend = trend_observation(
            price_change_pct=0.2,
            higher_high=False,
            higher_low=False,
            lower_high=False,
            lower_low=False,
            trend_bias=TrendBias.NEUTRAL,
            trend_strength=25,
            distance_from_range_pct=0.2,
            moving_average_alignment=TrendBias.NEUTRAL,
            slope=0.02,
        )
        structure = structure_observation(
            structure_break=StructureBreak.NONE,
            higher_timeframe_bias=TrendBias.NEUTRAL,
            current_price=100,
            range_low=95,
            range_high=105,
        )

        opinion = evaluate(trend, structure)

        self.assertEqual(opinion.direction, Direction.NEUTRAL)
        self.assertEqual(opinion.state, TrendState.RANGE.value)

    def test_bullish_correction_inside_bearish_htf_trend(self):
        structure = structure_observation(
            structure_break=StructureBreak.NONE,
            higher_timeframe_bias=TrendBias.BEARISH,
        )

        opinion = evaluate(structure=structure)

        self.assertEqual(opinion.direction, Direction.BULLISH)
        self.assertEqual(opinion.state, TrendState.CORRECTION.value)

    def test_bearish_correction_inside_bullish_htf_trend(self):
        trend = trend_observation(
            price_change_pct=-5,
            higher_high=False,
            higher_low=False,
            lower_high=True,
            lower_low=True,
            trend_bias=TrendBias.BEARISH,
            moving_average_alignment=TrendBias.BEARISH,
            slope=-1,
        )
        structure = structure_observation(
            structure_break=StructureBreak.NONE,
            higher_timeframe_bias=TrendBias.BULLISH,
        )

        opinion = evaluate(trend, structure)

        self.assertEqual(opinion.direction, Direction.BEARISH)
        self.assertEqual(opinion.state, TrendState.CORRECTION.value)

    def test_bullish_reversal_developing(self):
        trend = trend_observation(trend_bias=TrendBias.BEARISH)
        structure = structure_observation(
            structure_break=StructureBreak.BULLISH_CHOCH,
            higher_timeframe_bias=TrendBias.BEARISH,
        )

        opinion = evaluate(trend, structure)

        self.assertEqual(opinion.direction, Direction.BULLISH)
        self.assertEqual(opinion.state, TrendState.REVERSAL.value)
        self.assertLessEqual(opinion.confidence, 70)

    def test_bearish_reversal_developing(self):
        trend = trend_observation(
            trend_bias=TrendBias.BULLISH,
            moving_average_alignment=TrendBias.BEARISH,
            higher_high=False,
            higher_low=False,
            lower_high=True,
            lower_low=True,
            price_change_pct=-5,
            slope=-1,
        )
        structure = structure_observation(
            structure_break=StructureBreak.BEARISH_CHOCH,
            higher_timeframe_bias=TrendBias.BULLISH,
        )

        opinion = evaluate(trend, structure)

        self.assertEqual(opinion.direction, Direction.BEARISH)
        self.assertEqual(opinion.state, TrendState.REVERSAL.value)

    def test_confirmed_continuation_with_bos(self):
        opinion = evaluate()
        self.assertEqual(opinion.state, TrendState.TREND.value)
        self.assertTrue(opinion.metadata["classification_details"]["continuation_confirmed"])

    def test_choch_alone_does_not_force_reversal(self):
        trend = trend_observation(
            price_change_pct=-5,
            higher_high=False,
            higher_low=False,
            lower_high=True,
            lower_low=True,
            trend_bias=TrendBias.BEARISH,
            moving_average_alignment=TrendBias.BEARISH,
            slope=-1,
        )
        structure = structure_observation(
            structure_break=StructureBreak.BULLISH_CHOCH,
            higher_timeframe_bias=TrendBias.BEARISH,
        )

        opinion = evaluate(trend, structure)

        self.assertNotEqual(opinion.state, TrendState.REVERSAL.value)
        self.assertTrue(any("unconfirmed" in warning for warning in opinion.warnings))

    def test_mixed_direction_returns_neutral(self):
        trend = trend_observation(
            price_change_pct=0,
            higher_high=True,
            higher_low=True,
            lower_high=True,
            lower_low=True,
            trend_bias=TrendBias.NEUTRAL,
            moving_average_alignment=TrendBias.NEUTRAL,
            slope=0,
        )
        structure = structure_observation(
            structure_break=StructureBreak.NONE,
            higher_timeframe_bias=TrendBias.NEUTRAL,
        )
        opinion = evaluate(trend, structure)
        self.assertEqual(opinion.direction, Direction.NEUTRAL)

    def test_low_quality_returns_unknown_and_low_confidence(self):
        trend = trend_observation(quality=30)
        structure = structure_observation(quality=30)

        opinion = evaluate(trend, structure)

        self.assertEqual(opinion.state, TrendState.UNKNOWN.value)
        self.assertLessEqual(opinion.confidence, 30)
        self.assertTrue(any("quality" in warning.lower() for warning in opinion.warnings))

    def test_timestamp_mismatch_warns_and_reduces_confidence(self):
        aligned = evaluate()
        stale_structure = structure_observation(
            observed_at=OBSERVED_AT + timedelta(seconds=900)
        )

        stale = evaluate(structure=stale_structure)

        self.assertLess(stale.confidence, aligned.confidence)
        self.assertTrue(any("timestamps" in warning for warning in stale.warnings))

    def test_same_asset_is_required(self):
        with self.assertRaisesRegex(ValueError, "same asset"):
            evaluate(structure=structure_observation(asset="ETH"))

    def test_same_timeframe_is_required(self):
        with self.assertRaisesRegex(ValueError, "same timeframe"):
            evaluate(structure=structure_observation(timeframe="1h"))

    def test_unsupported_trend_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "TrendObservation version 2"):
            evaluate(trend=trend_observation(version=2))

    def test_unsupported_structure_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "StructureObservation version 2"):
            evaluate(structure=structure_observation(version=2))

    def test_invalid_input_types_are_rejected(self):
        expert = TrendExpert()
        with self.assertRaises(TypeError):
            expert.evaluate(None, structure_observation(), timestamp=OUTPUT_AT)
        with self.assertRaises(TypeError):
            expert.evaluate(trend_observation(), None, timestamp=OUTPUT_AT)

    def test_fixed_timestamp_is_preserved_and_normalized_to_utc(self):
        supplied = datetime(2026, 7, 14, 14, 5, tzinfo=timezone(timedelta(hours=2)))
        opinion = evaluate(timestamp=supplied)
        self.assertEqual(opinion.timestamp, OUTPUT_AT)
        self.assertIs(opinion.timestamp.tzinfo, timezone.utc)

    def test_naive_output_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            evaluate(timestamp=datetime(2026, 7, 14, 12, 5))

    def test_input_observations_remain_unchanged(self):
        trend = trend_observation()
        structure = structure_observation()
        before_trend = trend.to_dict()
        before_structure = structure.to_dict()

        evaluate(trend, structure)

        self.assertEqual(trend.to_dict(), before_trend)
        self.assertEqual(structure.to_dict(), before_structure)


class TrendExpertScoringTests(unittest.TestCase):
    def test_bullish_support_metadata_matches_formula(self):
        opinion = evaluate()
        expected = 100 * (25 + 15 + 12 + 12 + 10 + 5 + 20 + 15) / 117
        self.assertAlmostEqual(opinion.metadata["bullish_support"], expected, places=6)
        self.assertEqual(opinion.metadata["bearish_support"], 0.0)

    def test_bearish_support_metadata_matches_formula(self):
        trend = trend_observation(
            price_change_pct=-5,
            higher_high=False,
            higher_low=False,
            lower_high=True,
            lower_low=True,
            trend_bias=TrendBias.BEARISH,
            moving_average_alignment=TrendBias.BEARISH,
            slope=-1,
        )
        structure = structure_observation(
            structure_break=StructureBreak.BEARISH_BOS,
            higher_timeframe_bias=TrendBias.BEARISH,
        )
        opinion = evaluate(trend, structure)
        expected = 100 * (25 + 15 + 12 + 12 + 10 + 5 + 20 + 15) / 117
        self.assertAlmostEqual(opinion.metadata["bearish_support"], expected, places=6)
        self.assertEqual(opinion.metadata["bullish_support"], 0.0)

    def test_directional_lead_threshold_is_applied(self):
        policy = TrendExpertPolicy(direction_lead_threshold=100)
        opinion = evaluate(expert=TrendExpert(policy))
        self.assertEqual(opinion.direction, Direction.NEUTRAL)

    def test_score_and_confidence_are_bounded(self):
        opinion = evaluate()
        self.assertGreaterEqual(opinion.score, 0)
        self.assertLessEqual(opinion.score, 100)
        self.assertGreaterEqual(opinion.confidence, 0)
        self.assertLessEqual(opinion.confidence, 100)

    def test_quality_formula(self):
        opinion = evaluate(
            trend_observation(quality=80), structure_observation(quality=50)
        )
        self.assertEqual(opinion.quality, 68.0)

    def test_contradictory_flags_reduce_confidence(self):
        clean = evaluate()
        contradictory = evaluate(
            trend=trend_observation(lower_high=True, lower_low=True)
        )
        self.assertLess(contradictory.confidence, clean.confidence)

    def test_bos_increases_continuation_strength(self):
        with_bos = evaluate()
        without_bos = evaluate(
            structure=structure_observation(structure_break=StructureBreak.NONE)
        )
        self.assertGreater(with_bos.score, without_bos.score)

    def test_conflicting_bos_adds_warning(self):
        opinion = evaluate(
            structure=structure_observation(structure_break=StructureBreak.BEARISH_BOS)
        )
        self.assertTrue(any("conflicts" in warning for warning in opinion.warnings))

    def test_htf_alignment_increases_confidence(self):
        aligned = evaluate()
        neutral_htf = evaluate(
            structure=structure_observation(higher_timeframe_bias=TrendBias.NEUTRAL)
        )
        self.assertGreater(aligned.confidence, neutral_htf.confidence)

    def test_structure_quality_increases_confidence(self):
        strong = evaluate(structure=structure_observation(structure_quality=100))
        weak = evaluate(structure=structure_observation(structure_quality=20))
        self.assertGreater(strong.confidence, weak.confidence)

    def test_policy_is_frozen_and_validated(self):
        policy = TrendExpertPolicy()
        with self.assertRaises(Exception):
            policy.reason_limit = 20
        with self.assertRaises(ValueError):
            TrendExpertPolicy(direction_lead_threshold=101)
        with self.assertRaises(ValueError):
            TrendExpertPolicy(supported_versions=(1, 2))


class TrendExpertExplainabilityTests(unittest.TestCase):
    def test_reasons_are_deterministic(self):
        first = evaluate()
        second = evaluate()
        self.assertEqual(first.reasons, second.reasons)
        self.assertLessEqual(len(first.reasons), TrendExpert().policy.reason_limit)

    def test_warnings_are_deterministic_and_deduplicated(self):
        trend = trend_observation(
            quality=30,
            higher_high=True,
            lower_high=True,
            higher_low=True,
            lower_low=True,
        )
        structure = structure_observation(
            quality=70,
            observed_at=OBSERVED_AT + timedelta(seconds=900),
        )
        first = evaluate(trend, structure)
        second = evaluate(trend, structure)
        self.assertEqual(first.warnings, second.warnings)
        self.assertEqual(len(first.warnings), len(set(first.warnings)))

    def test_metadata_is_json_serializable(self):
        payload = evaluate().to_dict()
        encoded = json.dumps(payload)
        self.assertIn("trend_observation_id", encoded)

    def test_metadata_contains_observation_ids(self):
        opinion = evaluate()
        self.assertEqual(opinion.metadata["trend_observation_id"], "trend-btc-4h-001")
        self.assertEqual(
            opinion.metadata["structure_observation_id"], "structure-btc-4h-001"
        )

    def test_metadata_contains_no_raw_observations(self):
        def contains_observation(value):
            if isinstance(value, (TrendObservation, StructureObservation)):
                return True
            if isinstance(value, dict):
                return any(contains_observation(item) for item in value.values())
            if isinstance(value, (tuple, list)):
                return any(contains_observation(item) for item in value)
            return False

        self.assertFalse(contains_observation(evaluate().metadata))

    def test_unsupported_timeframe_semantics_add_warning(self):
        trend = trend_observation(timeframe="session")
        structure = structure_observation(timeframe="session")
        opinion = evaluate(trend, structure)
        self.assertTrue(any("Timeframe semantics" in warning for warning in opinion.warnings))


class TrendExpertRegressionAndArchitectureTests(unittest.TestCase):
    def test_output_is_expert_opinion(self):
        self.assertIsInstance(evaluate(), ExpertOpinion)

    def test_expert_opinion_round_trip(self):
        opinion = evaluate()
        self.assertEqual(ExpertOpinion.from_dict(opinion.to_dict()), opinion)

    def test_market_state_engine_accepts_trend_expert_output(self):
        opinion = evaluate()
        state = MarketStateEngine().synthesize([opinion], timestamp=OUTPUT_AT)
        self.assertEqual(state.direction, Direction.BULLISH)
        self.assertEqual(state.trend, TrendState.TREND)

    def test_expert_package_has_only_allowed_import_roots(self):
        package = Path("app/intelligence/experts")
        allowed_roots = {
            "app.intelligence.contracts",
            "app.intelligence.experts",
            "app.intelligence.observations",
            "dataclasses",
            "datetime",
            "math",
            "numbers",
            "re",
            "typing",
        }
        for path in package.rglob("*.py"):
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
