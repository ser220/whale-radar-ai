"""Focused tests for PS-2 availability-aware candidate construction."""

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from app.intelligence.early_bird import (
    EarlyBirdCandidateBuilder,
    EarlyBirdCandidateBuildResult,
    EarlyBirdFactorValue,
    FactorAvailability,
)


UTC = timezone.utc
NOW = datetime(2026, 7, 15, 14, 0, tzinfo=UTC)
FACTOR_NAMES = (
    "whale_activity",
    "open_interest_change",
    "funding_divergence",
    "volume_expansion",
    "relative_strength",
    "liquidity_event",
    "structure_event",
    "momentum_shift",
)


def factor(
    factor_name,
    availability=FactorAvailability.AVAILABLE,
    score=70,
    observed_at=NOW,
    source="normalized_test_source",
    quality=80,
    reason=None,
    metadata=None,
):
    if availability is not FactorAvailability.AVAILABLE:
        score = None
    return EarlyBirdFactorValue(
        factor_name=factor_name,
        availability=availability,
        score=score,
        observed_at=observed_at,
        source=source,
        quality=quality,
        reason=reason,
        metadata={} if metadata is None else metadata,
    )


def all_available():
    return tuple(
        factor(
            factor_name,
            score=10 * (index + 1),
            quality=60 + index,
        )
        for index, factor_name in enumerate(FACTOR_NAMES)
    )


def build(values, **overrides):
    arguments = {
        "candidate_id": "candidate-btc-1",
        "asset": "btcusdt",
        "observed_at": NOW,
        "source": "availability_aware_builder",
        "fast_event_ids": ("fast-1",),
        "observation_ids": ("observation-1",),
        "metadata": {"window": "1h", "nested": {"valid": True}},
    }
    arguments.update(overrides)
    return EarlyBirdCandidateBuilder().build(values, **arguments)


def runtime_imports():
    tree = ast.parse(
        Path("app/intelligence/early_bird/builder.py").read_text(
            encoding="utf-8"
        )
    )
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


class CandidateBuilderTests(unittest.TestCase):
    def test_valid_build_with_all_factors_available(self):
        result = build(all_available())
        self.assertEqual(FACTOR_NAMES, result.available_factors)
        self.assertEqual((), result.missing_factors)
        self.assertEqual(100.0, result.candidate.data_completeness_score)

    def test_valid_partial_build_synthesizes_missing_factors(self):
        result = build((factor("funding_divergence"),))
        self.assertEqual(("funding_divergence",), result.available_factors)
        self.assertEqual(7, len(result.missing_factors))
        self.assertEqual(
            FactorAvailability.MISSING,
            result.factor_values["whale_activity"].availability,
        )
        self.assertEqual(
            tuple(name for name in FACTOR_NAMES if name != "funding_divergence"),
            result.metadata["synthesized_missing_factors"],
        )

    def test_missing_factor_is_not_a_measured_zero(self):
        result = build(
            (
                factor("whale_activity"),
                factor("open_interest_change", FactorAvailability.MISSING),
            )
        )
        missing = result.factor_values["open_interest_change"]
        self.assertIsNone(missing.score)
        self.assertEqual(0.0, result.candidate.open_interest_change_score)
        self.assertIn("structural placeholder 0.0", " ".join(result.warnings))

    def test_stale_factor_is_excluded_from_quality(self):
        result = build(
            (
                factor("whale_activity", quality=80),
                factor(
                    "funding_divergence",
                    FactorAvailability.STALE,
                    quality=100,
                ),
            )
        )
        self.assertEqual(80.0, result.candidate.quality)
        self.assertEqual(("funding_divergence",), result.stale_factors)

    def test_unsupported_is_excluded_from_completeness_denominator(self):
        values = [factor("whale_activity")]
        values.append(
            factor("liquidity_event", FactorAvailability.UNSUPPORTED)
        )
        values.extend(
            factor(name, FactorAvailability.MISSING)
            for name in FACTOR_NAMES
            if name not in {"whale_activity", "liquidity_event"}
        )
        result = build(values)
        self.assertEqual(14.285714, result.candidate.data_completeness_score)

    def test_error_is_excluded_from_scores(self):
        result = build(
            (
                factor("whale_activity", score=75),
                factor("funding_divergence", FactorAvailability.ERROR),
            )
        )
        self.assertEqual(0.0, result.candidate.funding_divergence_score)
        self.assertIsNone(result.factor_values["funding_divergence"].score)
        self.assertEqual(("funding_divergence",), result.error_factors)

    def test_all_unsupported_is_rejected(self):
        values = tuple(
            factor(name, FactorAvailability.UNSUPPORTED) for name in FACTOR_NAMES
        )
        with self.assertRaisesRegex(ValueError, "all factors are UNSUPPORTED"):
            build(values)

    def test_no_available_factor_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one AVAILABLE"):
            build((factor("whale_activity", FactorAvailability.MISSING),))

    def test_empty_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            build(())

    def test_unknown_factor_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown factor"):
            build((factor("unknown_factor"),))

    def test_duplicate_factor_is_rejected(self):
        value = factor("whale_activity")
        with self.assertRaisesRegex(ValueError, "duplicate factor"):
            build((value, value))

    def test_invalid_factor_type_is_rejected(self):
        with self.assertRaises(TypeError):
            build((object(),))

    def test_generator_is_accepted(self):
        result = build(factor(name) for name in FACTOR_NAMES[:2])
        self.assertEqual(
            ("whale_activity", "open_interest_change"),
            result.available_factors,
        )

    def test_iterable_is_materialized_once(self):
        class OnePassIterable:
            def __init__(self):
                self.iterations = 0

            def __iter__(self):
                self.iterations += 1
                if self.iterations > 1:
                    raise AssertionError("iterable consumed more than once")
                yield factor("whale_activity")

        values = OnePassIterable()
        build(values)
        self.assertEqual(1, values.iterations)

    def test_candidate_fields_are_mapped_by_canonical_name(self):
        result = build(all_available())
        candidate = result.candidate
        self.assertEqual(10.0, candidate.whale_activity_score)
        self.assertEqual(20.0, candidate.open_interest_change_score)
        self.assertEqual(30.0, candidate.funding_divergence_score)
        self.assertEqual(40.0, candidate.volume_expansion_score)
        self.assertEqual(50.0, candidate.relative_strength_score)
        self.assertEqual(60.0, candidate.liquidity_event_score)
        self.assertEqual(70.0, candidate.structure_event_score)
        self.assertEqual(80.0, candidate.momentum_shift_score)

    def test_factor_mapping_and_status_groups_use_canonical_order(self):
        result = build(
            (
                factor("momentum_shift"),
                factor("whale_activity"),
                factor("liquidity_event", FactorAvailability.UNSUPPORTED),
            )
        )
        self.assertEqual(FACTOR_NAMES, tuple(result.factor_values))
        self.assertEqual(
            ("whale_activity", "momentum_shift"),
            result.available_factors,
        )

    def test_structural_placeholder_policy_is_in_result_metadata(self):
        result = build((factor("whale_activity"),))
        policy = result.metadata["builder_policy"]
        self.assertEqual(0.0, policy["structural_placeholder"])
        self.assertEqual(
            FactorAvailability.MISSING,
            result.factor_values["open_interest_change"].availability,
        )

    def test_completeness_formula(self):
        values = (
            factor("whale_activity"),
            factor("funding_divergence"),
            factor("liquidity_event", FactorAvailability.UNSUPPORTED),
        )
        result = build(values)
        self.assertEqual(28.571429, result.candidate.data_completeness_score)

    def test_quality_is_arithmetic_mean_of_available_quality(self):
        result = build(
            (
                factor("whale_activity", quality=80),
                factor("funding_divergence", quality=60),
            )
        )
        self.assertEqual(70.0, result.candidate.quality)

    def test_missing_available_quality_uses_fallback(self):
        result = build(
            (
                factor("whale_activity", quality=90),
                factor("funding_divergence", quality=None),
            )
        )
        self.assertEqual(70.0, result.candidate.quality)
        self.assertTrue(
            any("quality fallback 50.0" in warning for warning in result.warnings)
        )

    def test_freshness_uses_minimum_linear_hour_score(self):
        result = build(
            (
                factor("whale_activity", observed_at=NOW),
                factor(
                    "funding_divergence",
                    observed_at=NOW - timedelta(minutes=30),
                ),
            )
        )
        self.assertEqual(50.0, result.candidate.freshness_score)

    def test_freshness_is_bounded_at_zero(self):
        result = build(
            (factor("whale_activity", observed_at=NOW - timedelta(hours=2)),)
        )
        self.assertEqual(0.0, result.candidate.freshness_score)

    def test_candidate_timestamp_is_normalized_to_utc(self):
        offset_time = datetime(
            2026,
            7,
            15,
            17,
            0,
            tzinfo=timezone(timedelta(hours=3)),
        )
        result = build((factor("whale_activity"),), observed_at=offset_time)
        self.assertEqual(NOW, result.candidate.observed_at)
        self.assertIs(UTC, result.candidate.observed_at.tzinfo)

    def test_naive_candidate_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            build(
                (factor("whale_activity"),),
                observed_at=datetime(2026, 7, 15, 14, 0),
            )

    def test_candidate_id_asset_and_source_validation_is_preserved(self):
        for field_name, value in (
            ("candidate_id", ""),
            ("asset", ""),
            ("source", ""),
        ):
            with self.subTest(field_name=field_name), self.assertRaises(ValueError):
                build((factor("whale_activity"),), **{field_name: value})
        self.assertEqual(
            "BTCUSDT",
            build((factor("whale_activity"),), asset=" btcusdt ").candidate.asset,
        )

    def test_warnings_are_deterministic_across_input_order(self):
        first = factor("whale_activity", quality=None)
        second = factor("funding_divergence", FactorAvailability.STALE)
        self.assertEqual(
            build((first, second)).warnings,
            build((second, first)).warnings,
        )

    def test_warnings_are_deduplicated(self):
        warnings = build((factor("funding_divergence"),)).warnings
        self.assertEqual(len(warnings), len(set(warnings)))

    def test_no_whale_warning(self):
        warnings = build((factor("funding_divergence"),)).warnings
        self.assertIn("No whale factor is available.", warnings)

    def test_one_factor_warning(self):
        warnings = build((factor("whale_activity"),)).warnings
        self.assertIn("Only one factor is available.", warnings)

    def test_low_completeness_warning(self):
        warnings = build((factor("whale_activity"),)).warnings
        self.assertTrue(any("completeness is low" in item for item in warnings))

    def test_no_close_timestamp_warning(self):
        warnings = build(
            (
                factor(
                    "whale_activity",
                    observed_at=NOW - timedelta(minutes=20),
                ),
            )
        ).warnings
        self.assertTrue(any("within 15 minutes" in item for item in warnings))

    def test_source_artifact_ids_are_preserved(self):
        result = build(
            (factor("whale_activity"),),
            fast_event_ids=("fast-1", "fast-2"),
            observation_ids=("observation-1", "observation-2"),
        )
        self.assertEqual(("fast-1", "fast-2"), result.candidate.fast_event_ids)
        self.assertEqual(
            ("observation-1", "observation-2"),
            result.candidate.observation_ids,
        )

    def test_duplicate_artifact_ids_follow_candidate_rejection_policy(self):
        with self.assertRaises(ValueError):
            build(
                (factor("whale_activity"),),
                fast_event_ids=("fast-1", "fast-1"),
            )

    def test_metadata_is_frozen_and_defensively_copied(self):
        metadata = {"nested": {"values": [1, 2]}}
        result = build((factor("whale_activity"),), metadata=metadata)
        metadata["nested"]["values"].append(3)
        self.assertEqual((1, 2), result.candidate.metadata["nested"]["values"])
        self.assertEqual(
            (1, 2),
            result.metadata["candidate_metadata"]["nested"]["values"],
        )
        with self.assertRaises(TypeError):
            result.metadata["new"] = "value"

    def test_build_result_and_factor_mapping_are_immutable(self):
        result = build((factor("whale_activity"),))
        with self.assertRaises(FrozenInstanceError):
            result.warnings = ()
        with self.assertRaises(TypeError):
            result.factor_values["whale_activity"] = factor("whale_activity")

    def test_serialization_round_trip(self):
        original = build(
            (
                factor("whale_activity", metadata={"captured_at": NOW}),
                factor("liquidity_event", FactorAvailability.UNSUPPORTED),
            )
        )
        restored = EarlyBirdCandidateBuildResult.from_dict(original.to_dict())
        self.assertEqual(original, restored)
        self.assertIs(
            FactorAvailability.AVAILABLE,
            restored.factor_values["whale_activity"].availability,
        )
        self.assertIs(UTC, restored.candidate.observed_at.tzinfo)

    def test_input_factor_objects_are_not_mutated(self):
        original = factor("whale_activity", metadata={"values": [1, 2]})
        before = original.to_dict()
        build((original,))
        self.assertEqual(before, original.to_dict())

    def test_result_contains_no_direction_or_trade_fields(self):
        names = {item.name for item in fields(EarlyBirdCandidateBuildResult)}
        forbidden = {
            "direction",
            "recommendation",
            "signal",
            "buy",
            "sell",
            "entry",
            "target",
            "stop_loss",
            "execution",
        }
        self.assertTrue(names.isdisjoint(forbidden))


class DependencyBoundaryTests(unittest.TestCase):
    def test_runtime_imports_only_standard_library_and_local_early_bird(self):
        imports = runtime_imports()
        allowed = {
            "collections.abc",
            "dataclasses",
            "datetime",
            "types",
            "typing",
            "app.intelligence.early_bird.availability",
            "app.intelligence.early_bird.models",
        }
        self.assertTrue(set(imports).issubset(allowed), imports)

    def test_runtime_imports_no_forbidden_dependencies(self):
        imports = tuple(name.lower() for name in runtime_imports())
        forbidden = (
            "provider",
            "exchange",
            "telegram",
            "database",
            "repository",
            "pipeline",
            "expert",
            "market_state",
            "requests",
            "urllib",
            "socket",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertFalse(any(token in name for name in imports), imports)


if __name__ == "__main__":
    unittest.main()
