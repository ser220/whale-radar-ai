"""Focused tests for WR-036 Early Bird Foundation, Phase 1."""

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from app.intelligence.early_bird import (
    EarlyBirdAssessment,
    EarlyBirdCandidate,
    EarlyBirdEngine,
    EarlyBirdFactor,
    EarlyBirdPolicy,
)


UTC = timezone.utc
NOW = datetime(2026, 7, 15, 4, 0, tzinfo=UTC)


def make_candidate(candidate_id="candidate-1", asset="btcusdt", **overrides):
    values = {
        "candidate_id": candidate_id,
        "asset": asset,
        "observed_at": NOW,
        "source": "normalized_test_facts",
        "quality": 90,
        "whale_activity_score": 80,
        "open_interest_change_score": 60,
        "funding_divergence_score": 40,
        "volume_expansion_score": 50,
        "relative_strength_score": 70,
        "liquidity_event_score": 45,
        "structure_event_score": 30,
        "momentum_shift_score": 25,
        "freshness_score": 90,
        "data_completeness_score": 90,
        "fast_event_ids": ("fast-1",),
        "observation_ids": ("observation-1",),
        "metadata": {"providers_present": ["normalized_source"]},
    }
    values.update(overrides)
    return EarlyBirdCandidate(**values)


def make_assessment(**overrides):
    values = {
        "assessment_id": "early-bird:candidate-1:v1",
        "candidate_id": "candidate-1",
        "asset": "BTCUSDT",
        "evaluated_at": NOW,
        "opportunity_score": 60,
        "priority_score": 70,
        "maturity_score": 30,
        "quality": 90,
        "rank": None,
        "reasons": ("The asset deserves attention.",),
        "warnings": (),
        "factor_contributions": {
            "whale_activity": {
                "score": 80,
                "weight": 0.25,
                "weighted_contribution": 20,
            }
        },
        "source_event_ids": ("fast-1",),
        "source_observation_ids": ("observation-1",),
        "metadata": {"policy_version": 1},
    }
    values.update(overrides)
    return EarlyBirdAssessment(**values)


class CandidateContractTests(unittest.TestCase):
    def test_valid_candidate(self):
        candidate = make_candidate()
        self.assertEqual("candidate-1", candidate.candidate_id)
        self.assertEqual(90.0, candidate.quality)

    def test_candidate_is_immutable(self):
        candidate = make_candidate()
        with self.assertRaises(FrozenInstanceError):
            candidate.quality = 50

    def test_asset_is_normalized(self):
        self.assertEqual("BTCUSDT", make_candidate(asset=" btcusdt ").asset)

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            make_candidate(observed_at=datetime(2026, 7, 15, 4, 0))

    def test_timestamp_is_normalized_to_utc(self):
        offset = timezone(timedelta(hours=3))
        observed = datetime(2026, 7, 15, 7, 0, tzinfo=offset)
        candidate = make_candidate(observed_at=observed)
        self.assertEqual(NOW, candidate.observed_at)
        self.assertIs(UTC, candidate.observed_at.tzinfo)

    def test_score_boundaries_are_accepted(self):
        candidate = make_candidate(
            quality=0,
            whale_activity_score=100,
            open_interest_change_score=0,
            funding_divergence_score=100,
            volume_expansion_score=0,
            relative_strength_score=100,
            liquidity_event_score=0,
            structure_event_score=100,
            momentum_shift_score=0,
            freshness_score=100,
            data_completeness_score=0,
        )
        self.assertEqual(0.0, candidate.quality)
        self.assertEqual(100.0, candidate.whale_activity_score)

    def test_out_of_range_scores_are_rejected(self):
        for value in (-0.1, 100.1, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                make_candidate(quality=value)

    def test_boolean_numerics_are_rejected(self):
        with self.assertRaises(TypeError):
            make_candidate(freshness_score=True)

    def test_metadata_is_defensively_frozen(self):
        metadata = {"nested": {"values": [1, 2]}}
        candidate = make_candidate(metadata=metadata)
        metadata["nested"]["values"].append(3)
        self.assertEqual((1, 2), candidate.metadata["nested"]["values"])
        with self.assertRaises(TypeError):
            candidate.metadata["new"] = "value"

    def test_non_serializable_metadata_is_rejected(self):
        with self.assertRaises(TypeError):
            make_candidate(metadata={"object": object()})

    def test_candidate_serialization_round_trip(self):
        original = make_candidate(
            metadata={
                "factor": EarlyBirdFactor.WHALE_ACTIVITY,
                "recorded_at": NOW,
                "set": {"b", "a"},
            }
        )
        restored = EarlyBirdCandidate.from_dict(original.to_dict())
        self.assertEqual(original, restored)
        self.assertEqual(["a", "b"], original.to_dict()["metadata"]["set"])
        self.assertEqual("whale_activity", original.metadata["factor"])
        self.assertEqual(NOW.isoformat(), original.metadata["recorded_at"])

    def test_duplicate_stable_references_are_rejected(self):
        with self.assertRaises(ValueError):
            make_candidate(fast_event_ids=("fast-1", "fast-1"))

    def test_candidate_contains_no_direction_or_trade_fields(self):
        names = {item.name for item in fields(EarlyBirdCandidate)}
        forbidden = {
            "direction",
            "recommendation",
            "signal",
            "buy",
            "sell",
            "long",
            "short",
            "entry",
            "tp",
            "sl",
            "execution",
        }
        self.assertTrue(names.isdisjoint(forbidden))


class AssessmentContractTests(unittest.TestCase):
    def test_valid_assessment(self):
        assessment = make_assessment()
        self.assertEqual("early-bird:candidate-1:v1", assessment.assessment_id)

    def test_assessment_is_immutable(self):
        assessment = make_assessment()
        with self.assertRaises(FrozenInstanceError):
            assessment.rank = 1

    def test_assessment_score_boundaries(self):
        assessment = make_assessment(
            opportunity_score=0,
            priority_score=100,
            maturity_score=0,
            quality=100,
        )
        self.assertEqual(0.0, assessment.opportunity_score)
        self.assertEqual(100.0, assessment.priority_score)

    def test_assessment_rank_validation(self):
        self.assertEqual(1, make_assessment(rank=1).rank)
        with self.assertRaises(ValueError):
            make_assessment(rank=0)
        with self.assertRaises(TypeError):
            make_assessment(rank=True)

    def test_assessment_serialization_round_trip(self):
        original = make_assessment(rank=2)
        restored = EarlyBirdAssessment.from_dict(original.to_dict())
        self.assertEqual(original, restored)
        self.assertEqual(2, restored.rank)

    def test_assessment_collections_are_deeply_immutable(self):
        assessment = make_assessment()
        with self.assertRaises(TypeError):
            assessment.factor_contributions["new"] = {}
        with self.assertRaises(TypeError):
            assessment.factor_contributions["whale_activity"]["score"] = 0

    def test_assessment_contains_no_direction_or_trade_fields(self):
        names = {item.name for item in fields(EarlyBirdAssessment)}
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


class PolicyTests(unittest.TestCase):
    def test_default_opportunity_weights_are_exact(self):
        policy = EarlyBirdPolicy()
        self.assertEqual(0.25, policy.whale_activity_weight)
        self.assertEqual(0.15, policy.open_interest_change_weight)
        self.assertEqual(0.10, policy.funding_divergence_weight)
        self.assertEqual(1.0, sum((
            policy.whale_activity_weight,
            policy.open_interest_change_weight,
            policy.funding_divergence_weight,
            policy.volume_expansion_weight,
            policy.relative_strength_weight,
            policy.liquidity_event_weight,
            policy.structure_event_weight,
            policy.momentum_shift_weight,
        )))

    def test_default_priority_weights_are_exact(self):
        policy = EarlyBirdPolicy()
        self.assertEqual(
            (0.45, 0.25, 0.20, 0.10),
            (
                policy.priority_opportunity_weight,
                policy.priority_freshness_weight,
                policy.priority_urgency_weight,
                policy.priority_data_quality_weight,
            ),
        )

    def test_required_policy_defaults_are_explicit(self):
        policy = EarlyBirdPolicy()
        self.assertEqual(50.0, policy.minimum_quality_threshold)
        self.assertEqual(60.0, policy.minimum_completeness_threshold)
        self.assertEqual(30.0, policy.stale_freshness_threshold)
        self.assertEqual(85.0, policy.over_mature_threshold)
        self.assertEqual(5, policy.reason_limit)
        self.assertEqual(7, policy.warning_limit)
        self.assertEqual(20, policy.maximum_results)
        self.assertEqual(1, policy.policy_version)

    def test_policy_is_immutable(self):
        policy = EarlyBirdPolicy()
        with self.assertRaises(FrozenInstanceError):
            policy.maximum_results = 1

    def test_invalid_weight_group_is_rejected(self):
        with self.assertRaises(ValueError):
            EarlyBirdPolicy(whale_activity_weight=0.20)

    def test_boolean_policy_values_are_rejected(self):
        with self.assertRaises(TypeError):
            EarlyBirdPolicy(reason_limit=True)


class EngineScoringTests(unittest.TestCase):
    def setUp(self):
        self.engine = EarlyBirdEngine()

    def test_whale_led_case_is_early_and_explainable(self):
        candidate = make_candidate(
            whale_activity_score=100,
            open_interest_change_score=20,
            funding_divergence_score=50,
            volume_expansion_score=15,
            relative_strength_score=45,
            liquidity_event_score=70,
            structure_event_score=10,
            momentum_shift_score=10,
            freshness_score=100,
        )
        result = self.engine.evaluate_candidate(candidate, timestamp=NOW)
        self.assertIn(
            "Unusual whale activity is the strongest opportunity factor.",
            result.reasons,
        )
        self.assertLess(result.maturity_score, 35)

    def test_oi_volume_relative_strength_case_is_detected(self):
        candidate = make_candidate(
            whale_activity_score=0,
            quality=100,
            data_completeness_score=100,
            open_interest_change_score=95,
            volume_expansion_score=90,
            relative_strength_score=90,
            funding_divergence_score=60,
            liquidity_event_score=10,
            structure_event_score=50,
            momentum_shift_score=60,
        )
        result = self.engine.evaluate_candidate(candidate, timestamp=NOW)
        self.assertGreater(result.opportunity_score, 50)
        self.assertIn("Open-interest participation is expanding.", result.reasons)

    def test_low_quality_degrades_opportunity(self):
        high = self.engine.evaluate_candidate(make_candidate(quality=100), timestamp=NOW)
        low = self.engine.evaluate_candidate(make_candidate(quality=25), timestamp=NOW)
        self.assertLess(low.opportunity_score, high.opportunity_score)
        self.assertLess(low.priority_score, high.priority_score)
        self.assertIn(
            "Candidate data quality is below the policy threshold.", low.warnings
        )

    def test_incomplete_data_warning(self):
        result = self.engine.evaluate_candidate(
            make_candidate(data_completeness_score=30), timestamp=NOW
        )
        self.assertIn("Candidate data is incomplete.", result.warnings)

    def test_stale_warning(self):
        result = self.engine.evaluate_candidate(
            make_candidate(freshness_score=10), timestamp=NOW
        )
        self.assertIn("Candidate event is stale.", result.warnings)

    def test_over_mature_warning(self):
        result = self.engine.evaluate_candidate(
            make_candidate(
                structure_event_score=100,
                momentum_shift_score=100,
                volume_expansion_score=100,
                open_interest_change_score=100,
                freshness_score=0,
            ),
            timestamp=NOW,
        )
        self.assertGreaterEqual(result.maturity_score, 85)
        self.assertIn(
            "The opportunity appears over-mature for early attention.",
            result.warnings,
        )

    def test_one_factor_concentration_warning(self):
        candidate = make_candidate(
            whale_activity_score=100,
            open_interest_change_score=0,
            funding_divergence_score=0,
            volume_expansion_score=0,
            relative_strength_score=0,
            liquidity_event_score=0,
            structure_event_score=0,
            momentum_shift_score=0,
        )
        result = self.engine.evaluate_candidate(candidate, timestamp=NOW)
        self.assertIn(
            "Opportunity is driven almost entirely by one factor.", result.warnings
        )

    def test_no_whale_warning(self):
        result = self.engine.evaluate_candidate(
            make_candidate(whale_activity_score=0), timestamp=NOW
        )
        self.assertIn(
            "No whale activity is present in this whale-first assessment.",
            result.warnings,
        )

    def test_insufficient_independent_factors_warning(self):
        candidate = make_candidate(
            whale_activity_score=20,
            open_interest_change_score=0,
            funding_divergence_score=0,
            volume_expansion_score=0,
            relative_strength_score=0,
            liquidity_event_score=0,
            structure_event_score=0,
            momentum_shift_score=0,
        )
        result = self.engine.evaluate_candidate(candidate, timestamp=NOW)
        self.assertIn(
            "Insufficient independent opportunity factors are present.",
            result.warnings,
        )

    def test_reasons_are_deterministic(self):
        candidate = make_candidate()
        first = self.engine.evaluate_candidate(candidate, timestamp=NOW)
        second = self.engine.evaluate_candidate(candidate, timestamp=NOW)
        self.assertEqual(first.reasons, second.reasons)

    def test_warnings_are_deterministic(self):
        candidate = make_candidate(
            quality=10,
            data_completeness_score=10,
            freshness_score=10,
            whale_activity_score=0,
        )
        first = self.engine.evaluate_candidate(candidate, timestamp=NOW)
        second = self.engine.evaluate_candidate(candidate, timestamp=NOW)
        self.assertEqual(first.warnings, second.warnings)

    def test_factor_contributions_are_explainable(self):
        result = self.engine.evaluate_candidate(make_candidate(), timestamp=NOW)
        whale = result.factor_contributions[EarlyBirdFactor.WHALE_ACTIVITY.value]
        self.assertEqual(80.0, whale["score"])
        self.assertEqual(0.25, whale["weight"])
        self.assertEqual(20.0, whale["weighted_contribution"])

    def test_evaluation_is_deterministic_with_fixed_timestamp(self):
        candidate = make_candidate()
        self.assertEqual(
            self.engine.evaluate_candidate(candidate, timestamp=NOW),
            self.engine.evaluate_candidate(candidate, timestamp=NOW),
        )

    def test_explicit_overextension_proxy_affects_maturity_only(self):
        base = make_candidate(metadata={})
        extended = make_candidate(metadata={"overextension_score": 100})
        first = self.engine.evaluate_candidate(base, timestamp=NOW)
        second = self.engine.evaluate_candidate(extended, timestamp=NOW)
        self.assertGreater(second.maturity_score, first.maturity_score)
        self.assertEqual(second.opportunity_score, first.opportunity_score)
        self.assertEqual(second.priority_score, first.priority_score)

    def test_invalid_explicit_overextension_proxy_is_rejected(self):
        candidate = make_candidate(metadata={"overextension_score": True})
        with self.assertRaises(TypeError):
            self.engine.evaluate_candidate(candidate, timestamp=NOW)

    def test_output_scores_are_bounded(self):
        result = self.engine.evaluate_candidate(
            make_candidate(
                quality=100,
                whale_activity_score=100,
                open_interest_change_score=100,
                funding_divergence_score=100,
                volume_expansion_score=100,
                relative_strength_score=100,
                liquidity_event_score=100,
                structure_event_score=100,
                momentum_shift_score=100,
                freshness_score=100,
                data_completeness_score=100,
            ),
            timestamp=NOW,
        )
        for value in (
            result.opportunity_score,
            result.priority_score,
            result.maturity_score,
            result.quality,
        ):
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)

    def test_evaluation_does_not_mutate_candidate(self):
        candidate = make_candidate()
        snapshot = candidate.to_dict()
        self.engine.evaluate_candidate(candidate, timestamp=NOW)
        self.assertEqual(snapshot, candidate.to_dict())

    def test_invalid_candidate_type_is_rejected(self):
        with self.assertRaises(TypeError):
            self.engine.evaluate_candidate({}, timestamp=NOW)


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.engine = EarlyBirdEngine()
        self.first = make_candidate("candidate-a", "BTCUSDT")
        self.second = make_candidate(
            "candidate-b", "ETHUSDT", whale_activity_score=60
        )

    def test_list_input(self):
        result = self.engine.rank_candidates([self.first, self.second], timestamp=NOW)
        self.assertEqual(2, len(result))

    def test_tuple_input(self):
        result = self.engine.rank_candidates((self.first, self.second), timestamp=NOW)
        self.assertEqual(2, len(result))

    def test_generator_input(self):
        result = self.engine.rank_candidates(
            (item for item in (self.first, self.second)), timestamp=NOW
        )
        self.assertEqual(2, len(result))

    def test_empty_input(self):
        self.assertEqual((), self.engine.rank_candidates([], timestamp=NOW))

    def test_duplicate_candidate_id_is_rejected(self):
        duplicate = make_candidate("candidate-a", "ETHUSDT")
        with self.assertRaises(ValueError):
            self.engine.rank_candidates([self.first, duplicate], timestamp=NOW)

    def test_ranking_is_stable_across_input_order(self):
        forward = self.engine.rank_candidates(
            [self.first, self.second], timestamp=NOW
        )
        reverse = self.engine.rank_candidates(
            [self.second, self.first], timestamp=NOW
        )
        self.assertEqual(
            tuple(item.candidate_id for item in forward),
            tuple(item.candidate_id for item in reverse),
        )

    def test_priority_descending(self):
        fresh = make_candidate("fresh", freshness_score=100)
        stale = make_candidate("stale", freshness_score=0)
        ranked = self.engine.rank_candidates([stale, fresh], timestamp=NOW)
        self.assertEqual("fresh", ranked[0].candidate_id)
        self.assertGreaterEqual(ranked[0].priority_score, ranked[1].priority_score)

    def test_opportunity_tie_uses_deterministic_asset_order(self):
        btc = make_candidate("candidate-z", "BTCUSDT")
        eth = make_candidate("candidate-a", "ETHUSDT")
        ranked = self.engine.rank_candidates([eth, btc], timestamp=NOW)
        self.assertEqual(("BTCUSDT", "ETHUSDT"), tuple(item.asset for item in ranked))

    def test_lower_maturity_wins_exact_priority_and_opportunity_tie(self):
        early = make_candidate("early", metadata={"overextension_score": 0})
        mature = make_candidate("mature", metadata={"overextension_score": 100})
        ranked = self.engine.rank_candidates([mature, early], timestamp=NOW)
        self.assertEqual(ranked[0].priority_score, ranked[1].priority_score)
        self.assertEqual(ranked[0].opportunity_score, ranked[1].opportunity_score)
        self.assertEqual("early", ranked[0].candidate_id)

    def test_limit_behavior(self):
        result = self.engine.rank_candidates(
            [self.first, self.second], limit=1, timestamp=NOW
        )
        self.assertEqual(1, len(result))

    def test_policy_maximum_results_caps_explicit_limit(self):
        engine = EarlyBirdEngine(EarlyBirdPolicy(maximum_results=1))
        result = engine.rank_candidates(
            [self.first, self.second], limit=10, timestamp=NOW
        )
        self.assertEqual(1, len(result))

    def test_rank_assignment_occurs_after_sorting(self):
        ranked = self.engine.rank_candidates([self.second, self.first], timestamp=NOW)
        self.assertEqual((1, 2), tuple(item.rank for item in ranked))

    def test_same_asset_with_distinct_ids_is_allowed(self):
        other = make_candidate("candidate-c", "BTCUSDT")
        ranked = self.engine.rank_candidates([self.first, other], timestamp=NOW)
        self.assertEqual(2, len(ranked))

    def test_invalid_iterable_member_is_rejected(self):
        with self.assertRaises(TypeError):
            self.engine.rank_candidates([self.first, {}], timestamp=NOW)

    def test_invalid_limit_is_rejected(self):
        for value in (0, -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.engine.rank_candidates([], limit=value, timestamp=NOW)
        with self.assertRaises(TypeError):
            self.engine.rank_candidates([], limit=True, timestamp=NOW)

    def test_ranking_does_not_mutate_candidates(self):
        snapshots = (self.first.to_dict(), self.second.to_dict())
        self.engine.rank_candidates([self.first, self.second], timestamp=NOW)
        self.assertEqual(snapshots, (self.first.to_dict(), self.second.to_dict()))


class DependencyBoundaryTests(unittest.TestCase):
    def test_runtime_imports_only_standard_library_and_own_package(self):
        package = Path(__file__).parent / "app" / "intelligence" / "early_bird"
        for path in package.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("app."):
                        self.assertTrue(
                            node.module.startswith("app.intelligence.early_bird"),
                            "forbidden local import in {0}: {1}".format(path, node.module),
                        )
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertFalse(alias.name.startswith("app."))


if __name__ == "__main__":
    unittest.main()
