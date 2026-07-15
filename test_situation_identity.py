"""Focused tests for the deterministic PS-4 Situation Identity Engine."""

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import MappingProxyType
import unittest

from app.intelligence.early_bird import EmergingStage
from app.intelligence.timeline import (
    MarketSituationTimeline,
    MarketSituationTimelineEntry,
    SituationDNA,
    SituationIdentityEngine,
    SituationIdentityResult,
)


UTC = timezone.utc
NOW = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)


def make_dna(**overrides):
    values = {
        "whale_activity": None,
        "funding_divergence": None,
        "volume_expansion": 60.0,
        "structure_event": 45.0,
        "momentum_shift": 40.0,
        "relative_strength": 55.0,
        "open_interest_change": None,
        "liquidity_event": None,
        "completeness": 66.67,
        "quality": 78.0,
        "freshness": 90.0,
        "opportunity": 65.0,
        "priority": 70.0,
        "maturity": 35.0,
        "emergence": 72.0,
        "horizon": 80.0,
        "detection_confidence": 76.0,
        "factor_availability": {
            "funding_divergence": "MISSING",
            "liquidity_event": "UNSUPPORTED",
            "momentum_shift": "AVAILABLE",
            "open_interest_change": "UNSUPPORTED",
            "relative_strength": "AVAILABLE",
            "structure_event": "AVAILABLE",
            "volume_expansion": "AVAILABLE",
            "whale_activity": "MISSING",
        },
        "metadata": {},
    }
    values.update(overrides)
    return SituationDNA(**values)


def make_entry(
    timeline_id,
    entry_id,
    created_at,
    stage=EmergingStage.EMERGING,
    dna=None,
    supporting=("volume_expansion", "structure_event"),
    limiting=("whale_activity",),
):
    return MarketSituationTimelineEntry(
        entry_id=entry_id,
        timeline_id=timeline_id,
        created_at=created_at,
        stage=stage,
        dna=dna or make_dna(),
        supporting_factors=supporting,
        limiting_factors=limiting,
        expected_events=(),
        observed_events=(),
        missing_expected_events=(),
        unexpected_events=(),
        transition_reason="Fixture stage recorded.",
        source_assessment_id="assessment-{0}".format(entry_id),
        source_candidate_id="candidate-{0}".format(entry_id),
        source_situation_id=None,
        metadata={},
    )


def make_timeline(
    timeline_id="existing-timeline",
    asset="LINK",
    stage=EmergingStage.EMERGING,
    at=NOW,
    dna=None,
    supporting=("volume_expansion", "structure_event"),
    limiting=("whale_activity",),
    version=3,
    metadata=None,
):
    entry = make_entry(
        timeline_id,
        "entry-{0}".format(timeline_id),
        at,
        stage=stage,
        dna=dna,
        supporting=supporting,
        limiting=limiting,
    )
    return MarketSituationTimeline(
        timeline_id=timeline_id,
        asset=asset,
        created_at=at,
        updated_at=at,
        entries=(entry,),
        current_stage=stage,
        version=version,
        metadata={} if metadata is None else metadata,
    )


def make_candidate(
    asset="LINK",
    stage=EmergingStage.BUILDING,
    at=NOW + timedelta(minutes=15),
    dna=None,
    supporting=("volume_expansion", "structure_event"),
    limiting=("whale_activity",),
    version=1,
):
    return make_timeline(
        timeline_id="candidate-timeline",
        asset=asset,
        stage=stage,
        at=at,
        dna=dna,
        supporting=supporting,
        limiting=limiting,
        version=version,
    )


class SituationIdentityResultTests(unittest.TestCase):
    def test_valid_matched_result(self):
        result = SituationIdentityResult(
            matched=True,
            confidence=88,
            reason="Deterministic continuity matched.",
            matched_timeline_id="existing",
            matched_version=3,
            candidate_timeline_id="candidate",
            metadata={"criteria": {"dna": 90}},
        )
        self.assertTrue(result.matched)
        self.assertEqual(88.0, result.confidence)

    def test_match_reference_invariants(self):
        with self.assertRaises(ValueError):
            SituationIdentityResult(
                True, 80, "match", None, 1, "candidate", {}
            )
        with self.assertRaises(ValueError):
            SituationIdentityResult(
                False, 20, "new", "existing", 1, "candidate", {}
            )

    def test_result_is_immutable_and_deeply_frozen(self):
        result = SituationIdentityEngine().evaluate(
            make_timeline(),
            make_candidate(),
        )
        self.assertIsInstance(result.metadata, MappingProxyType)
        self.assertIsInstance(result.metadata["criteria"], MappingProxyType)
        with self.assertRaises(FrozenInstanceError):
            result.matched = False
        with self.assertRaises(TypeError):
            result.metadata["new"] = 1

    def test_result_serialization_round_trip(self):
        result = SituationIdentityEngine().evaluate(
            make_timeline(),
            make_candidate(),
        )
        restored = SituationIdentityResult.from_dict(result.to_dict())
        self.assertEqual(result, restored)

    def test_result_has_no_trade_direction_outcome_or_learning_fields(self):
        names = {item.name for item in fields(SituationIdentityResult)}
        self.assertFalse(
            names
            & {
                "trade",
                "direction",
                "outcome",
                "learning",
                "opportunity",
                "execution",
            }
        )


class HardRejectionTests(unittest.TestCase):
    def assert_hard_rejection(self, result, code):
        self.assertFalse(result.matched)
        self.assertEqual(0.0, result.confidence)
        self.assertTrue(result.metadata["hard_rejection"])
        self.assertEqual(code, result.metadata["rejection_code"])
        self.assertIsNone(result.matched_timeline_id)

    def test_asset_mismatch(self):
        result = SituationIdentityEngine().evaluate(
            make_timeline(asset="LINK"),
            make_candidate(asset="ETH"),
        )
        self.assert_hard_rejection(result, "asset_mismatch")
        self.assertIn("Different assets", result.reason)

    def test_existing_exhausted(self):
        result = SituationIdentityEngine().evaluate(
            make_timeline(stage=EmergingStage.EXHAUSTED),
            make_candidate(),
        )
        self.assert_hard_rejection(result, "existing_timeline_exhausted")

    def test_existing_closed_by_explicit_boolean(self):
        result = SituationIdentityEngine().evaluate(
            make_timeline(metadata={"closed": True}),
            make_candidate(),
        )
        self.assert_hard_rejection(result, "existing_timeline_closed")

    def test_existing_closed_by_status(self):
        result = SituationIdentityEngine().evaluate(
            make_timeline(metadata={"status": "CLOSED"}),
            make_candidate(),
        )
        self.assert_hard_rejection(result, "existing_timeline_closed")

    def test_time_gap_exceeds_configured_threshold(self):
        result = SituationIdentityEngine(max_time_gap=timedelta(hours=2)).evaluate(
            make_timeline(),
            make_candidate(at=NOW + timedelta(hours=2, seconds=1)),
        )
        self.assert_hard_rejection(result, "time_gap_exceeded")

    def test_time_regression_is_rejected(self):
        result = SituationIdentityEngine().evaluate(
            make_timeline(at=NOW),
            make_candidate(at=NOW - timedelta(seconds=1)),
        )
        self.assert_hard_rejection(result, "time_regression")


class SoftContinuityTests(unittest.TestCase):
    def test_same_situation_matches_existing_identity(self):
        existing = make_timeline(version=4)
        result = SituationIdentityEngine().evaluate(existing, make_candidate())
        self.assertTrue(result.matched)
        self.assertEqual(existing.timeline_id, result.matched_timeline_id)
        self.assertEqual(4, result.matched_version)
        self.assertGreaterEqual(result.confidence, 65.0)
        self.assertFalse(result.metadata["hard_rejection"])

    def test_discontinuous_dna_and_factors_create_new_situation(self):
        new_dna = make_dna(
            whale_activity=95,
            funding_divergence=90,
            volume_expansion=None,
            structure_event=None,
            momentum_shift=None,
            relative_strength=None,
            opportunity=5,
            priority=10,
            maturity=95,
            emergence=5,
            horizon=10,
            detection_confidence=20,
        )
        result = SituationIdentityEngine().evaluate(
            make_timeline(),
            make_candidate(
                stage=EmergingStage.MATURE,
                dna=new_dna,
                supporting=("whale_activity",),
                limiting=("volume_expansion",),
            ),
        )
        self.assertFalse(result.matched)
        self.assertLess(result.confidence, 65.0)
        self.assertEqual("new_situation", result.metadata["decision"])

    def test_one_step_stage_progression_is_fully_compatible(self):
        result = SituationIdentityEngine().evaluate(
            make_timeline(stage=EmergingStage.EMERGING),
            make_candidate(stage=EmergingStage.BUILDING),
        )
        self.assertEqual(100.0, result.metadata["criteria"]["stage_compatibility"])

    def test_stage_regression_is_scored_not_hard_rejected(self):
        result = SituationIdentityEngine().evaluate(
            make_timeline(stage=EmergingStage.BUILDING),
            make_candidate(stage=EmergingStage.EMERGING),
        )
        self.assertFalse(result.metadata["hard_rejection"])
        self.assertEqual(55.0, result.metadata["criteria"]["stage_compatibility"])

    def test_dna_continuity_uses_shared_measured_factors(self):
        same = SituationIdentityEngine().evaluate(
            make_timeline(),
            make_candidate(),
        )
        changed = SituationIdentityEngine().evaluate(
            make_timeline(),
            make_candidate(dna=make_dna(volume_expansion=0, structure_event=0)),
        )
        self.assertGreater(
            same.metadata["criteria"]["dna_continuity"],
            changed.metadata["criteria"]["dna_continuity"],
        )

    def test_supporting_and_limiting_continuity_are_independent(self):
        result = SituationIdentityEngine().evaluate(
            make_timeline(),
            make_candidate(
                supporting=("volume_expansion",),
                limiting=("funding_divergence",),
            ),
        )
        criteria = result.metadata["criteria"]
        self.assertEqual(50.0, criteria["supporting_factor_continuity"])
        self.assertEqual(0.0, criteria["limiting_factor_continuity"])

    def test_time_continuity_decreases_with_age(self):
        engine = SituationIdentityEngine(max_time_gap=timedelta(hours=6))
        near = engine.evaluate(make_timeline(), make_candidate(at=NOW + timedelta(minutes=5)))
        far = engine.evaluate(make_timeline(), make_candidate(at=NOW + timedelta(hours=5)))
        self.assertGreater(
            near.metadata["criteria"]["time_continuity"],
            far.metadata["criteria"]["time_continuity"],
        )

    def test_reason_generation_is_deterministic(self):
        engine = SituationIdentityEngine()
        first = engine.evaluate(make_timeline(), make_candidate())
        second = engine.evaluate(make_timeline(), make_candidate())
        self.assertEqual(first, second)
        self.assertIn("continuity", first.reason)
        self.assertIn("DNA", first.reason)

    def test_inputs_are_not_modified(self):
        existing = make_timeline()
        candidate = make_candidate()
        before = (existing.to_dict(), candidate.to_dict())
        SituationIdentityEngine().evaluate(existing, candidate)
        self.assertEqual(before, (existing.to_dict(), candidate.to_dict()))


class ValidationAndBoundaryTests(unittest.TestCase):
    def test_new_timeline_must_be_version_one_with_one_entry(self):
        with self.assertRaises(ValueError):
            SituationIdentityEngine().evaluate(
                make_timeline(),
                make_candidate(version=2),
            )

    def test_existing_timeline_must_have_an_entry(self):
        empty = MarketSituationTimeline(
            timeline_id="empty",
            asset="LINK",
            created_at=NOW,
            updated_at=NOW,
            entries=(),
            current_stage=EmergingStage.UNKNOWN,
            version=1,
            metadata={},
        )
        with self.assertRaises(ValueError):
            SituationIdentityEngine().evaluate(empty, make_candidate())

    def test_policy_configuration_validation(self):
        with self.assertRaises(ValueError):
            SituationIdentityEngine(max_time_gap=timedelta(0))
        with self.assertRaises(TypeError):
            SituationIdentityEngine(match_threshold=True)

    def test_identity_runtime_has_no_forbidden_imports(self):
        path = Path("app/intelligence/timeline/identity.py")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        forbidden = (
            "telegram",
            "database",
            "repository",
            "provider",
            "scanner",
            "exchange",
            "network",
            "requests",
            "httpx",
            "market_state",
            "experts",
            "decision",
            "learning",
        )
        self.assertFalse(
            any(part in name.lower() for name in imports for part in forbidden),
            imports,
        )


if __name__ == "__main__":
    unittest.main()
