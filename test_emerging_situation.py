"""Focused offline tests for PS-3 Step 4 Emerging Situation."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import unittest

from app.intelligence.early_bird import (
    EarlyBirdCandidateBuilder,
    EarlyBirdEngine,
    EarlyBirdExplainer,
    EarlyBirdFactorValue,
    EmergingSituation,
    EmergingSituationEngine,
    EmergingStage,
    FactorAvailability,
    format_emerging_situation,
)
from app.intelligence.early_bird.builder import CANONICAL_FACTOR_NAMES


UTC = timezone.utc
NOW = datetime(2026, 7, 15, 22, 0, tzinfo=UTC)

DEFAULT_SCORES = {
    "whale_activity": 60.0,
    "open_interest_change": 45.0,
    "funding_divergence": 50.0,
    "volume_expansion": 50.0,
    "relative_strength": 40.0,
    "liquidity_event": 30.0,
    "structure_event": 35.0,
    "momentum_shift": 30.0,
}


def make_inputs(
    asset="BTC",
    scores=None,
    statuses=None,
    quality=80.0,
    freshness=100.0,
    assessment_overrides=None,
):
    factor_scores = dict(DEFAULT_SCORES)
    factor_scores.update(scores or {})
    factor_statuses = {
        factor_name: FactorAvailability.AVAILABLE
        for factor_name in CANONICAL_FACTOR_NAMES
    }
    factor_statuses.update(statuses or {})
    age_seconds = (100.0 - freshness) / 100.0 * 3600.0
    measured_at = NOW - timedelta(seconds=age_seconds)
    values = []
    for factor_name in CANONICAL_FACTOR_NAMES:
        status = factor_statuses[factor_name]
        if status is FactorAvailability.AVAILABLE:
            values.append(
                EarlyBirdFactorValue(
                    factor_name,
                    status,
                    score=factor_scores[factor_name],
                    observed_at=measured_at,
                    source="offline-test",
                    quality=quality,
                )
            )
        else:
            values.append(
                EarlyBirdFactorValue(
                    factor_name,
                    status,
                    observed_at=(
                        measured_at
                        if status is FactorAvailability.STALE
                        else None
                    ),
                    source=(
                        "offline-test"
                        if status is FactorAvailability.STALE
                        else None
                    ),
                    quality=(
                        quality
                        if status is FactorAvailability.STALE
                        else None
                    ),
                    reason="Offline availability fixture.",
                )
            )
    build_result = EarlyBirdCandidateBuilder().build(
        values,
        candidate_id="emerging:{0}".format(asset.lower()),
        asset=asset,
        observed_at=NOW,
        source="offline-emerging-test",
    )
    assessment = EarlyBirdEngine().evaluate_candidate(
        build_result.candidate,
        timestamp=NOW,
    )
    if assessment_overrides:
        assessment = replace(assessment, **assessment_overrides)
    explanation = EarlyBirdExplainer().explain(assessment, build_result)
    return assessment, build_result, explanation


def evaluate(**kwargs):
    return EmergingSituationEngine().evaluate(
        *make_inputs(**kwargs),
        timestamp=NOW,
    )


class EmergingSituationModelTests(unittest.TestCase):
    def test_valid_emerging_situation(self):
        result = evaluate(
            assessment_overrides={
                "opportunity_score": 60.0,
                "priority_score": 65.0,
                "maturity_score": 20.0,
            }
        )
        self.assertEqual("BTC", result.asset)
        self.assertEqual(NOW, result.evaluated_at)
        self.assertGreater(result.emergence_score, 35.0)
        self.assertGreater(result.horizon_score, 60.0)

    def test_model_is_immutable_and_metadata_is_frozen(self):
        result = evaluate()
        with self.assertRaises(FrozenInstanceError):
            result.stage = EmergingStage.SEED
        with self.assertRaises(TypeError):
            result.metadata["new"] = True

    def test_serialization_round_trip(self):
        original = evaluate()
        restored = EmergingSituation.from_dict(original.to_dict())
        self.assertEqual(original, restored)
        self.assertEqual(original.stage.value, original.to_dict()["stage"])

    def test_asset_is_normalized_uppercase(self):
        result = evaluate(asset="link")
        self.assertEqual("LINK", result.asset)

    def test_naive_timestamp_is_rejected(self):
        inputs = make_inputs()
        with self.assertRaises(ValueError):
            EmergingSituationEngine().evaluate(
                *inputs,
                timestamp=datetime(2026, 7, 15, 22, 0),
            )

    def test_score_bounds_and_boolean_rejection(self):
        payload = evaluate().to_dict()
        for field_name in (
            "emergence_score",
            "horizon_score",
            "detection_confidence",
        ):
            invalid = dict(payload)
            invalid[field_name] = 101
            with self.subTest(field=field_name), self.assertRaises(ValueError):
                EmergingSituation.from_dict(invalid)
        invalid = dict(payload)
        invalid["horizon_score"] = True
        with self.assertRaises(TypeError):
            EmergingSituation.from_dict(invalid)

    def test_model_has_no_direction_or_trade_fields(self):
        names = {item.name for item in fields(EmergingSituation)}
        forbidden = {
            "direction",
            "recommendation",
            "signal",
            "buy",
            "sell",
            "long",
            "short",
            "entry",
            "target",
            "stop",
            "tp",
            "sl",
            "execution",
        }
        self.assertTrue(names.isdisjoint(forbidden))


class ScoreAndStageTests(unittest.TestCase):
    def test_high_emergence_and_high_horizon(self):
        result = evaluate(
            scores={
                "whale_activity": 80.0,
                "funding_divergence": 70.0,
                "volume_expansion": 35.0,
                "structure_event": 35.0,
                "momentum_shift": 30.0,
            },
            assessment_overrides={
                "opportunity_score": 65.0,
                "priority_score": 70.0,
                "maturity_score": 15.0,
            },
        )
        self.assertGreater(result.emergence_score, 60.0)
        self.assertGreater(result.horizon_score, 70.0)
        self.assertIs(EmergingStage.EMERGING, result.stage)

    def test_high_opportunity_can_have_low_horizon(self):
        result = evaluate(
            scores={"structure_event": 100.0},
            freshness=0.0,
            assessment_overrides={
                "opportunity_score": 95.0,
                "priority_score": 90.0,
                "maturity_score": 90.0,
            },
        )
        self.assertEqual(95.0, result.metadata["source_opportunity_score"])
        self.assertLess(result.horizon_score, 25.0)

    def test_low_opportunity_can_have_high_horizon(self):
        result = evaluate(
            scores={
                "structure_event": 20.0,
                "volume_expansion": 10.0,
                "momentum_shift": 10.0,
            },
            assessment_overrides={
                "opportunity_score": 10.0,
                "priority_score": 20.0,
                "maturity_score": 10.0,
            },
        )
        self.assertEqual(10.0, result.metadata["source_opportunity_score"])
        self.assertGreater(result.horizon_score, 75.0)

    def test_seed_stage(self):
        statuses = {
            factor_name: FactorAvailability.UNSUPPORTED
            for factor_name in CANONICAL_FACTOR_NAMES
            if factor_name != "structure_event"
        }
        result = evaluate(
            scores={"structure_event": 0.0},
            statuses=statuses,
            assessment_overrides={
                "opportunity_score": 0.0,
                "priority_score": 10.0,
                "maturity_score": 10.0,
            },
        )
        self.assertIs(EmergingStage.SEED, result.stage)

    def test_building_stage(self):
        result = evaluate(
            scores={"structure_event": 70.0},
            freshness=40.0,
            assessment_overrides={
                "opportunity_score": 70.0,
                "priority_score": 65.0,
                "maturity_score": 50.0,
            },
        )
        self.assertIs(EmergingStage.BUILDING, result.stage)

    def test_mature_stage(self):
        result = evaluate(
            scores={"structure_event": 90.0},
            freshness=20.0,
            assessment_overrides={
                "opportunity_score": 80.0,
                "priority_score": 70.0,
                "maturity_score": 75.0,
            },
        )
        self.assertIs(EmergingStage.MATURE, result.stage)

    def test_exhausted_stage(self):
        result = evaluate(
            scores={"structure_event": 100.0},
            freshness=0.0,
            assessment_overrides={
                "opportunity_score": 90.0,
                "priority_score": 75.0,
                "maturity_score": 90.0,
            },
        )
        self.assertIs(EmergingStage.EXHAUSTED, result.stage)

    def test_unknown_when_no_emergence_factor_is_available(self):
        statuses = {
            factor_name: FactorAvailability.MISSING
            for factor_name in (
                "whale_activity",
                "funding_divergence",
                "volume_expansion",
                "structure_event",
                "momentum_shift",
            )
        }
        result = evaluate(statuses=statuses)
        self.assertIs(EmergingStage.UNKNOWN, result.stage)
        self.assertEqual(0.0, result.emergence_score)
        self.assertTrue(
            any("No measured emergence factor" in item for item in result.warnings)
        )

    def test_low_detection_confidence_forces_unknown(self):
        statuses = {
            factor_name: FactorAvailability.MISSING
            for factor_name in CANONICAL_FACTOR_NAMES
            if factor_name != "structure_event"
        }
        result = evaluate(
            scores={"structure_event": 30.0},
            statuses=statuses,
            quality=0.0,
            freshness=0.0,
            assessment_overrides={
                "opportunity_score": 50.0,
                "priority_score": 40.0,
                "maturity_score": 20.0,
            },
        )
        self.assertLess(result.detection_confidence, 20.0)
        self.assertIs(EmergingStage.UNKNOWN, result.stage)


class InputAndFormulaTests(unittest.TestCase):
    def test_emergence_formula_is_exact(self):
        assessment, build_result, explanation = make_inputs()
        result = EmergingSituationEngine().evaluate(
            assessment,
            build_result,
            explanation,
            timestamp=NOW,
        )
        expected = round(
            0.55 * result.metadata["fresh_factor_strength"]
            + 0.20 * assessment.opportunity_score
            + 0.15 * build_result.candidate.freshness_score
            + 0.10 * result.metadata["independence_proxy"],
            6,
        )
        self.assertEqual(expected, result.emergence_score)

    def test_horizon_formula_is_exact(self):
        assessment, build_result, explanation = make_inputs()
        result = EmergingSituationEngine().evaluate(
            assessment,
            build_result,
            explanation,
            timestamp=NOW,
        )
        expected = round(
            0.50 * (100.0 - assessment.maturity_score)
            + 0.20 * build_result.candidate.freshness_score
            + 0.20 * result.metadata["early_structure_proxy"]
            + 0.10 * result.metadata["incomplete_confirmation_proxy"],
            6,
        )
        self.assertEqual(expected, result.horizon_score)

    def test_detection_confidence_formula_is_exact(self):
        assessment, build_result, explanation = make_inputs()
        result = EmergingSituationEngine().evaluate(
            assessment,
            build_result,
            explanation,
            timestamp=NOW,
        )
        expected = round(
            0.40 * build_result.candidate.data_completeness_score
            + 0.30 * build_result.candidate.quality
            + 0.20 * result.metadata["independent_factor_coverage"]
            + 0.10 * build_result.candidate.freshness_score,
            6,
        )
        self.assertEqual(expected, result.detection_confidence)

    def test_default_timestamp_is_source_deterministic(self):
        inputs = make_inputs()
        first = EmergingSituationEngine().evaluate(*inputs)
        second = EmergingSituationEngine().evaluate(*inputs)
        self.assertEqual(first, second)
        self.assertEqual(inputs[0].evaluated_at, first.evaluated_at)

    def test_only_available_emergence_factors_are_used(self):
        statuses = {
            "whale_activity": FactorAvailability.MISSING,
            "funding_divergence": FactorAvailability.STALE,
        }
        result = evaluate(
            scores={
                "whale_activity": 100.0,
                "funding_divergence": 100.0,
                "volume_expansion": 40.0,
                "structure_event": 40.0,
                "momentum_shift": 40.0,
            },
            statuses=statuses,
        )
        self.assertNotIn(
            "whale_activity",
            result.metadata["available_emergence_factors"],
        )
        self.assertNotIn(
            "funding_divergence",
            result.metadata["available_emergence_factors"],
        )

    def test_structural_placeholders_are_not_measurements(self):
        result = evaluate(
            statuses={"whale_activity": FactorAvailability.MISSING}
        )
        self.assertNotIn("whale_activity", result.supporting_factors)
        self.assertIn("whale_activity", result.missing_factors)

    def test_missing_factor_is_not_described_as_weak(self):
        result = evaluate(
            statuses={"momentum_shift": FactorAvailability.MISSING}
        )
        self.assertNotIn("Measured momentum remains weak.", result.limiting_factors)
        self.assertIn("momentum_shift", result.missing_factors)

    def test_stale_factor_is_excluded_from_strength(self):
        fresh = evaluate(scores={"funding_divergence": 100.0})
        stale = evaluate(
            scores={"funding_divergence": 100.0},
            statuses={"funding_divergence": FactorAvailability.STALE},
        )
        self.assertLess(stale.emergence_score, fresh.emergence_score)
        self.assertIn("funding_divergence", stale.stale_factors)

    def test_independence_proxy_uses_material_available_emergence_factors(self):
        one = evaluate(
            scores={
                "whale_activity": 30.0,
                "funding_divergence": 0.0,
                "volume_expansion": 0.0,
                "structure_event": 0.0,
                "momentum_shift": 1.0,
            }
        )
        four = evaluate(
            scores={
                "whale_activity": 30.0,
                "funding_divergence": 30.0,
                "volume_expansion": 30.0,
                "structure_event": 30.0,
                "momentum_shift": 1.0,
            }
        )
        self.assertEqual(25.0, one.metadata["independence_proxy"])
        self.assertEqual(100.0, four.metadata["independence_proxy"])

    def test_completeness_affects_detection_confidence(self):
        complete = evaluate()
        incomplete = evaluate(
            statuses={
                "whale_activity": FactorAvailability.MISSING,
                "funding_divergence": FactorAvailability.MISSING,
            }
        )
        self.assertLess(
            incomplete.detection_confidence,
            complete.detection_confidence,
        )

    def test_quality_affects_detection_confidence(self):
        low = evaluate(quality=20.0)
        high = evaluate(quality=90.0)
        self.assertLess(low.detection_confidence, high.detection_confidence)

    def test_freshness_affects_detection_confidence(self):
        stale = evaluate(freshness=0.0)
        fresh = evaluate(freshness=100.0)
        self.assertLess(stale.detection_confidence, fresh.detection_confidence)

    def test_high_maturity_reduces_horizon(self):
        early = evaluate(
            assessment_overrides={"maturity_score": 10.0}
        )
        late = evaluate(
            assessment_overrides={"maturity_score": 90.0}
        )
        self.assertLess(late.horizon_score, early.horizon_score)

    def test_moderate_structure_has_more_horizon_than_extreme_structure(self):
        moderate = evaluate(scores={"structure_event": 20.0})
        extreme = evaluate(scores={"structure_event": 100.0})
        self.assertGreater(
            moderate.metadata["early_structure_proxy"],
            extreme.metadata["early_structure_proxy"],
        )
        self.assertGreater(moderate.horizon_score, extreme.horizon_score)

    def test_incomplete_confirmation_requires_measured_confirmation(self):
        unavailable = evaluate(
            scores={"structure_event": 40.0},
            statuses={
                "volume_expansion": FactorAvailability.MISSING,
                "momentum_shift": FactorAvailability.MISSING,
            },
        )
        measured = evaluate(
            scores={
                "structure_event": 40.0,
                "volume_expansion": 10.0,
                "momentum_shift": 20.0,
            }
        )
        self.assertEqual(
            0.0,
            unavailable.metadata["incomplete_confirmation_proxy"],
        )
        self.assertGreater(
            measured.metadata["incomplete_confirmation_proxy"],
            0.0,
        )


class ExplanationAndOutputTests(unittest.TestCase):
    def test_supporting_factors_order_by_existing_weighted_contribution(self):
        result = evaluate(
            scores={
                "whale_activity": 80.0,
                "open_interest_change": 80.0,
                "volume_expansion": 50.0,
            }
        )
        self.assertEqual("whale_activity", result.supporting_factors[0])
        self.assertEqual("open_interest_change", result.supporting_factors[1])

    def test_limiting_factors_reasons_and_warnings_are_deterministic(self):
        first = evaluate(
            scores={"volume_expansion": 10.0, "momentum_shift": 10.0},
            statuses={"whale_activity": FactorAvailability.MISSING},
        )
        second = evaluate(
            scores={"volume_expansion": 10.0, "momentum_shift": 10.0},
            statuses={"whale_activity": FactorAvailability.MISSING},
        )
        self.assertEqual(first.limiting_factors, second.limiting_factors)
        self.assertEqual(first.reasons, second.reasons)
        self.assertEqual(first.warnings, second.warnings)
        self.assertEqual(len(first.warnings), len(set(first.warnings)))

    def test_identity_mismatch_is_rejected(self):
        assessment, build_result, _ = make_inputs("BTC")
        _, _, other_explanation = make_inputs("ETH")
        with self.assertRaises(ValueError):
            EmergingSituationEngine().evaluate(
                assessment,
                build_result,
                other_explanation,
                timestamp=NOW,
            )

    def test_inputs_are_not_mutated(self):
        inputs = make_inputs()
        before = tuple(item.to_dict() for item in inputs)
        EmergingSituationEngine().evaluate(*inputs, timestamp=NOW)
        after = tuple(item.to_dict() for item in inputs)
        self.assertEqual(before, after)

    def test_formatter_output(self):
        output = format_emerging_situation(evaluate(asset="LINK"))
        self.assertIn("LINK", output)
        self.assertIn("Emergence:", output)
        self.assertIn("Horizon:", output)
        self.assertIn("Stage:", output)
        self.assertIn("Detection confidence:", output)
        self.assertIn("Supporting factors:", output)
        self.assertIn("Limiting factors:", output)
        self.assertIn("Why:", output)

    def test_formatter_contains_no_trade_language_or_telegram_markup(self):
        output = format_emerging_situation(evaluate()).lower()
        forbidden = ("buy", "sell", "long", "short", "entry", "tp", "sl")
        for word in forbidden:
            with self.subTest(word=word):
                self.assertIsNone(re.search(r"\b{0}\b".format(word), output))
        self.assertNotIn("<b>", output)

    def test_runtime_dependency_boundary(self):
        tree = ast.parse(
            Path("app/intelligence/early_bird/emerging.py").read_text(
                encoding="utf-8"
            )
        )
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        application_imports = tuple(
            name for name in imports if name.startswith("app.")
        )
        self.assertEqual(
            (
                "app.intelligence.early_bird.availability",
                "app.intelligence.early_bird.builder",
                "app.intelligence.early_bird.explain",
                "app.intelligence.early_bird.models",
            ),
            application_imports,
        )
        forbidden = (
            "telegram",
            "provider",
            "scanner",
            "exchange",
            "funding_hub",
            "database",
            "repository",
            "market_state",
            "expert",
            "network",
        )
        self.assertFalse(
            any(token in name.lower() for token in forbidden for name in imports)
        )


if __name__ == "__main__":
    unittest.main()
