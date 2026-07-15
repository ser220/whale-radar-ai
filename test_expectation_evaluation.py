"""Focused offline tests for the PS-4 Step 6 expectation evaluator."""

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
import importlib
from pathlib import Path
from types import MappingProxyType
import unittest

from app.domain.candle import Candle
from app.intelligence.early_bird import EmergingStage
from app.intelligence.early_bird.scanner import EarlyBirdScanner
from app.intelligence.timeline import (
    ExpectationEvaluationPolicy,
    ExpectationEvaluationStatus,
    ExpectationKind,
    ExpectationStrength,
    MarketSituationTimeline,
    MarketSituationTimelineEntry,
    RealityGapType,
    SituationDNA,
    SituationExpectation,
    SituationExpectationEvaluation,
    SituationExpectationEvaluator,
    deterministic_evaluation_id,
    format_expectation_evaluation,
    format_expectation_evaluations,
)
from run_expectation_evaluation_demo import run_two_scan_expectation_evaluation


UTC = timezone.utc
NOW = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
FACTORS = (
    "whale_activity",
    "funding_divergence",
    "volume_expansion",
    "structure_event",
    "momentum_shift",
    "relative_strength",
    "open_interest_change",
    "liquidity_event",
)


def make_dna(**overrides):
    values = {
        "whale_activity": 70.0,
        "funding_divergence": None,
        "volume_expansion": 20.0,
        "structure_event": 55.0,
        "momentum_shift": 20.0,
        "relative_strength": 50.0,
        "open_interest_change": None,
        "liquidity_event": None,
        "completeness": 62.5,
        "quality": 80.0,
        "freshness": 90.0,
        "opportunity": 60.0,
        "priority": 65.0,
        "maturity": 30.0,
        "emergence": 65.0,
        "horizon": 80.0,
        "detection_confidence": 72.0,
        "factor_availability": {
            "whale_activity": "AVAILABLE",
            "funding_divergence": "MISSING",
            "volume_expansion": "AVAILABLE",
            "structure_event": "AVAILABLE",
            "momentum_shift": "AVAILABLE",
            "relative_strength": "AVAILABLE",
            "open_interest_change": "UNSUPPORTED",
            "liquidity_event": "UNSUPPORTED",
        },
        "metadata": {"fixture": True},
    }
    values.update(overrides)
    availability = dict(values["factor_availability"])
    values["factor_availability"] = availability
    for name in FACTORS:
        if availability[name] != "AVAILABLE":
            values[name] = None
    return SituationDNA(**values)


def make_entry(number, minutes, *, stage=EmergingStage.EMERGING, dna=None,
               supporting=("structure_event", "whale_activity")):
    return MarketSituationTimelineEntry(
        entry_id="entry-{0}".format(number),
        timeline_id="timeline-sol",
        created_at=NOW + timedelta(minutes=minutes),
        stage=stage,
        dna=dna or make_dna(),
        supporting_factors=supporting,
        limiting_factors=(),
        expected_events=(),
        observed_events=("fixture observation",),
        missing_expected_events=(),
        unexpected_events=(),
        transition_reason="Fixture entry recorded.",
        source_assessment_id="assessment-{0}".format(number),
        source_candidate_id="candidate-{0}".format(number),
        source_situation_id=None,
        metadata={},
    )


SOURCE_ENTRY = make_entry(1, 0)


def make_timeline(*later_entries, version=None, updated_at=None, asset="SOL",
                  timeline_id="timeline-sol"):
    entries = (SOURCE_ENTRY,) + tuple(later_entries)
    latest = entries[-1]
    return MarketSituationTimeline(
        timeline_id=timeline_id,
        asset=asset,
        created_at=NOW,
        updated_at=updated_at or latest.created_at,
        entries=entries,
        current_stage=latest.stage,
        version=version or len(entries),
        metadata={},
    )


def contract(rule_name="volume_confirmation", kind=ExpectationKind.CONFIRMATION,
             subject="volume_expansion", **extra):
    values = {
        "contract_version": "1",
        "rule_name": rule_name,
        "expectation_kind": kind.value,
        "subject": subject,
        "source_policy_version": 1,
        "source_timeline_version": 1,
        "source_stage": EmergingStage.EMERGING.value,
        "window_minutes": 60,
    }
    values.update(extra)
    return values


def volume_contract(**overrides):
    values = {
        "target_factor": "volume_expansion",
        "confirmation_threshold": 35.0,
        "structure_material_threshold": 35.0,
        "structure_contradiction_threshold": 35.0,
        "maturity_contradiction_threshold": 55.0,
        "minimum_coverage_ratio": 0.60,
    }
    values.update(overrides)
    return contract(**values)


def momentum_contract(**overrides):
    values = {
        "target_factor": "momentum_shift",
        "confirmation_threshold": 35.0,
        "initiating_factors": ("structure_event",),
        "initiating_factor_threshold": 35.0,
        "contradiction_threshold": 20.0,
        "minimum_coverage_ratio": 0.60,
    }
    values.update(overrides)
    return contract(rule_name="momentum_confirmation", subject="momentum_shift", **values)


def expectation_for(evaluation_contract=None, *, kind=ExpectationKind.CONFIRMATION,
                    subject="volume_expansion", source=SOURCE_ENTRY, **overrides):
    values = {
        "expectation_id": "expectation-fixture",
        "timeline_id": source.timeline_id,
        "timeline_version": 1,
        "asset": "SOL",
        "created_at": NOW,
        "window_start": NOW,
        "window_end": NOW + timedelta(hours=1),
        "kind": kind,
        "strength": ExpectationStrength.MEDIUM,
        "subject": subject,
        "description": "Structured future fact is expected.",
        "basis": ("stored source facts",),
        "fulfillment_criteria": ("presentation only",),
        "contradiction_criteria": ("presentation only",),
        "source_entry_id": source.entry_id,
        "source_stage": source.stage,
        "source_factor_values": {name: getattr(source.dna, name) for name in FACTORS},
        "source_factor_availability": {
            name: source.dna.factor_availability[name] for name in FACTORS
        },
        "metadata": (
            {"evaluation_contract": evaluation_contract}
            if evaluation_contract is not None else {}
        ),
    }
    values.update(overrides)
    return SituationExpectation(**values)


def evaluate(evaluation_contract, *entries, at=NOW + timedelta(minutes=61),
             kind=ExpectationKind.CONFIRMATION, subject="volume_expansion"):
    expectation = expectation_for(evaluation_contract, kind=kind, subject=subject)
    timeline = make_timeline(*entries, updated_at=at)
    return SituationExpectationEvaluator().evaluate(
        expectation, timeline, evaluated_at=at
    )


class EvaluationModelTests(unittest.TestCase):
    def make_model(self, **overrides):
        values = {
            "evaluation_id": "evaluation-1",
            "expectation_id": "expectation-1",
            "timeline_id": "timeline-sol",
            "source_timeline_version": 1,
            "evaluated_timeline_version": 2,
            "asset": "sol",
            "evaluated_at": NOW + timedelta(hours=1),
            "window_start": NOW,
            "window_end": NOW + timedelta(hours=1),
            "status": ExpectationEvaluationStatus.MISSING,
            "gap_type": RealityGapType.MISSING_EXPECTED_EVENT,
            "surprise_score": 50,
            "observed_facts": ("fact",),
            "fulfilled_criteria": (),
            "missing_criteria": ("missing",),
            "contradicted_criteria": (),
            "unexpected_events": (),
            "reason": "Window ended.",
            "source_expectation_snapshot": {"nested": {"items": [1]}},
            "evaluated_entry_ids": ("entry-2",),
            "metadata": {"policy": 1},
        }
        values.update(overrides)
        return SituationExpectationEvaluation(**values)

    def test_valid_model_normalizes_and_freezes(self):
        model = self.make_model()
        self.assertEqual("SOL", model.asset)
        self.assertIsInstance(model.metadata, MappingProxyType)
        self.assertIsInstance(model.source_expectation_snapshot["nested"], MappingProxyType)

    def test_model_is_immutable(self):
        model = self.make_model()
        with self.assertRaises(FrozenInstanceError):
            model.status = ExpectationEvaluationStatus.FULFILLED
        with self.assertRaises(TypeError):
            model.metadata["x"] = 1

    def test_model_round_trip(self):
        model = self.make_model()
        self.assertEqual(model, SituationExpectationEvaluation.from_dict(model.to_dict()))

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            self.make_model(evaluated_at=NOW.replace(tzinfo=None))

    def test_versions_and_scores_reject_booleans_and_bounds(self):
        for name, value in (("source_timeline_version", True),
                            ("evaluated_timeline_version", 0),
                            ("surprise_score", True),
                            ("surprise_score", 101)):
            with self.subTest(name=name), self.assertRaises((TypeError, ValueError)):
                self.make_model(**{name: value})

    def test_no_trade_or_profit_fields(self):
        names = {item.name for item in fields(SituationExpectationEvaluation)}
        self.assertFalse(names & {"buy", "sell", "tp", "sl", "direction", "profit_probability"})


class ValidationAndWindowTests(unittest.TestCase):
    def setUp(self):
        self.expectation = expectation_for(volume_contract())
        self.evaluator = SituationExpectationEvaluator()

    def test_timeline_and_asset_mismatch(self):
        with self.assertRaises(ValueError):
            self.evaluator.evaluate(self.expectation, make_timeline(timeline_id="other"))
        with self.assertRaises(ValueError):
            self.evaluator.evaluate(self.expectation, make_timeline(asset="ETH"))

    def test_version_regression_and_missing_source_entry(self):
        older = expectation_for(volume_contract(), timeline_version=2)
        with self.assertRaises(ValueError):
            self.evaluator.evaluate(older, make_timeline(version=1))
        empty_other = make_entry(2, 10)
        broken = MarketSituationTimeline(
            timeline_id="timeline-sol", asset="SOL", created_at=NOW,
            updated_at=empty_other.created_at, entries=(empty_other,),
            current_stage=empty_other.stage, version=2, metadata={},
        )
        with self.assertRaises(ValueError):
            self.evaluator.evaluate(self.expectation, broken)

    def test_naive_and_pre_creation_evaluated_at_rejected(self):
        with self.assertRaises(ValueError):
            self.evaluator.evaluate(self.expectation, make_timeline(), evaluated_at=NOW.replace(tzinfo=None))
        with self.assertRaises(ValueError):
            self.evaluator.evaluate(self.expectation, make_timeline(), evaluated_at=NOW - timedelta(seconds=1))

    def test_before_window_pending(self):
        expectation = expectation_for(
            volume_contract(),
            created_at=NOW,
            window_start=NOW + timedelta(minutes=5),
            window_end=NOW + timedelta(minutes=65),
        )
        result = self.evaluator.evaluate(expectation, make_timeline(), evaluated_at=NOW + timedelta(minutes=1))
        self.assertIs(result.status, ExpectationEvaluationStatus.PENDING)

    def test_inside_window_pending(self):
        entry = make_entry(2, 10, dna=make_dna(volume_expansion=25))
        result = self.evaluator.evaluate(self.expectation, make_timeline(entry), evaluated_at=entry.created_at)
        self.assertIs(result.status, ExpectationEvaluationStatus.PENDING)

    def test_only_future_entries_and_after_evaluation_are_ignored(self):
        conclusive = make_entry(2, 20, dna=make_dna(volume_expansion=50))
        result = self.evaluator.evaluate(
            self.expectation, make_timeline(conclusive, updated_at=conclusive.created_at),
            evaluated_at=NOW + timedelta(minutes=10),
        )
        self.assertIs(result.status, ExpectationEvaluationStatus.PENDING)
        self.assertEqual((), result.evaluated_entry_ids)

    def test_evidence_after_window_end_is_ignored(self):
        late = make_entry(2, 70, dna=make_dna(volume_expansion=50))
        result = self.evaluator.evaluate(
            self.expectation, make_timeline(late, updated_at=late.created_at),
            evaluated_at=late.created_at,
        )
        self.assertIs(result.status, ExpectationEvaluationStatus.EXPIRED)
        self.assertEqual((), result.evaluated_entry_ids)
        self.assertTrue(result.metadata["post_window_evidence_ignored"])

    def test_inputs_and_snapshot_are_not_mutated(self):
        entry = make_entry(2, 10, dna=make_dna(volume_expansion=50))
        timeline = make_timeline(entry)
        before_expectation = self.expectation.to_dict()
        before_timeline = timeline.to_dict()
        result = self.evaluator.evaluate(self.expectation, timeline, evaluated_at=entry.created_at)
        self.assertEqual(before_expectation, self.expectation.to_dict())
        self.assertEqual(before_timeline, timeline.to_dict())
        self.assertEqual(
            before_expectation,
            result.to_dict()["source_expectation_snapshot"],
        )

    def test_deterministic_evaluation_id_and_fact_order(self):
        one = make_entry(2, 10, dna=make_dna(volume_expansion=25))
        two = make_entry(3, 20, dna=make_dna(volume_expansion=30))
        timeline = make_timeline(one, two, updated_at=NOW + timedelta(minutes=61))
        first = self.evaluator.evaluate(self.expectation, timeline, evaluated_at=NOW + timedelta(minutes=61))
        second = self.evaluator.evaluate(self.expectation, timeline, evaluated_at=NOW + timedelta(minutes=61))
        self.assertEqual(first, second)
        self.assertEqual(first.evaluation_id, deterministic_evaluation_id(self.expectation, timeline, NOW + timedelta(minutes=61)))
        self.assertEqual(("entry-2", "entry-3"), first.evaluated_entry_ids)


class RuleEvaluationTests(unittest.TestCase):
    def test_volume_confirmation_fulfilled_and_missing(self):
        fulfilled = evaluate(volume_contract(), make_entry(2, 10, dna=make_dna(volume_expansion=40)), at=NOW + timedelta(minutes=10))
        missing = evaluate(volume_contract(), make_entry(2, 10, dna=make_dna(volume_expansion=25)))
        self.assertIs(fulfilled.status, ExpectationEvaluationStatus.FULFILLED)
        self.assertIs(missing.status, ExpectationEvaluationStatus.MISSING)

    def test_volume_unavailable_expired_and_contradicted(self):
        unavailable = make_dna(factor_availability=dict(make_dna().factor_availability, volume_expansion="MISSING"))
        expired = evaluate(volume_contract(), make_entry(2, 10, dna=unavailable))
        contradicted = evaluate(volume_contract(), make_entry(2, 10, dna=make_dna(volume_expansion=25, structure_event=10)), at=NOW + timedelta(minutes=10))
        self.assertIs(expired.status, ExpectationEvaluationStatus.EXPIRED)
        self.assertIs(contradicted.status, ExpectationEvaluationStatus.CONTRADICTED)

    def test_momentum_fulfilled_missing_and_contradicted(self):
        fulfilled = evaluate(momentum_contract(), make_entry(2, 10, dna=make_dna(momentum_shift=40)), kind=ExpectationKind.CONFIRMATION, subject="momentum_shift", at=NOW + timedelta(minutes=10))
        missing = evaluate(momentum_contract(), make_entry(2, 10, dna=make_dna(momentum_shift=25)), kind=ExpectationKind.CONFIRMATION, subject="momentum_shift")
        contradicted = evaluate(momentum_contract(), make_entry(2, 10, dna=make_dna(momentum_shift=25, structure_event=10)), kind=ExpectationKind.CONFIRMATION, subject="momentum_shift", at=NOW + timedelta(minutes=10))
        self.assertIs(fulfilled.status, ExpectationEvaluationStatus.FULFILLED)
        self.assertIs(missing.status, ExpectationEvaluationStatus.MISSING)
        self.assertIs(contradicted.status, ExpectationEvaluationStatus.CONTRADICTED)

    def test_factor_persistence_all_outcomes(self):
        persistence = contract(
            rule_name="factor_persistence", kind=ExpectationKind.FACTOR_PERSISTENCE,
            subject="whale_activity", target_factor="whale_activity",
            persistence_threshold=45.0, contradiction_threshold=25.0,
            minimum_required_later_entries=1,
        )
        fulfilled = evaluate(persistence, make_entry(2, 10, dna=make_dna(whale_activity=50)), kind=ExpectationKind.FACTOR_PERSISTENCE, subject="whale_activity", at=NOW + timedelta(minutes=10))
        contradicted = evaluate(persistence, make_entry(2, 10, dna=make_dna(whale_activity=10)), kind=ExpectationKind.FACTOR_PERSISTENCE, subject="whale_activity", at=NOW + timedelta(minutes=10))
        unavailable_dna = make_dna(factor_availability=dict(make_dna().factor_availability, whale_activity="MISSING"))
        expired = evaluate(persistence, make_entry(2, 10, dna=unavailable_dna), kind=ExpectationKind.FACTOR_PERSISTENCE, subject="whale_activity")
        self.assertIs(fulfilled.status, ExpectationEvaluationStatus.FULFILLED)
        self.assertIs(contradicted.status, ExpectationEvaluationStatus.CONTRADICTED)
        self.assertIs(expired.status, ExpectationEvaluationStatus.EXPIRED)

    def test_factor_appearance_all_outcomes(self):
        appearance = contract(
            rule_name="funding_appearance_after_structure_volume",
            kind=ExpectationKind.FACTOR_APPEARANCE, subject="funding_divergence",
            target_factor="funding_divergence", source_required_availability="MISSING",
            fulfillment_availability="AVAILABLE", missing_confirmation_availability="MISSING",
            disqualifying_availability_states=("ERROR", "STALE", "UNSUPPORTED"),
            minimum_required_later_entries=1,
        )
        available = make_dna(funding_divergence=50, factor_availability=dict(make_dna().factor_availability, funding_divergence="AVAILABLE"))
        error = make_dna(factor_availability=dict(make_dna().factor_availability, funding_divergence="ERROR"))
        fulfilled = evaluate(appearance, make_entry(2, 10, dna=available), kind=ExpectationKind.FACTOR_APPEARANCE, subject="funding_divergence", at=NOW + timedelta(minutes=10))
        missing = evaluate(appearance, make_entry(2, 10, dna=make_dna()), kind=ExpectationKind.FACTOR_APPEARANCE, subject="funding_divergence")
        expired = evaluate(appearance, make_entry(2, 10, dna=error), kind=ExpectationKind.FACTOR_APPEARANCE, subject="funding_divergence")
        self.assertIs(fulfilled.status, ExpectationEvaluationStatus.FULFILLED)
        self.assertIs(missing.status, ExpectationEvaluationStatus.MISSING)
        self.assertIs(expired.status, ExpectationEvaluationStatus.EXPIRED)

    def test_stage_advance_exact_missing_and_two_stage_jump(self):
        advance = contract(
            rule_name="stage_advance_emerging_to_building",
            kind=ExpectationKind.STAGE_ADVANCE, subject="stage",
            source_stage="EMERGING", expected_target_stage="BUILDING",
            incompatible_stages=("SEED", "MATURE", "EXHAUSTED"),
            minimum_required_later_entries=1,
        )
        exact = evaluate(advance, make_entry(2, 10, stage=EmergingStage.BUILDING), kind=ExpectationKind.STAGE_ADVANCE, subject="stage", at=NOW + timedelta(minutes=10))
        missing = evaluate(advance, make_entry(2, 10, stage=EmergingStage.EMERGING), kind=ExpectationKind.STAGE_ADVANCE, subject="stage")
        jump = evaluate(advance, make_entry(2, 10, stage=EmergingStage.MATURE), kind=ExpectationKind.STAGE_ADVANCE, subject="stage", at=NOW + timedelta(minutes=10))
        self.assertIs(exact.status, ExpectationEvaluationStatus.FULFILLED)
        self.assertIs(missing.status, ExpectationEvaluationStatus.MISSING)
        self.assertIs(jump.status, ExpectationEvaluationStatus.CONTRADICTED)

    def test_stage_persistence_fulfilled_and_contradicted(self):
        persistence = contract(
            rule_name="stage_persistence_emerging", kind=ExpectationKind.STAGE_PERSISTENCE,
            subject="stage", source_stage="EMERGING", required_stage="EMERGING",
            minimum_required_later_entries=1,
        )
        fulfilled = evaluate(persistence, make_entry(2, 10), kind=ExpectationKind.STAGE_PERSISTENCE, subject="stage", at=NOW + timedelta(minutes=10))
        contradicted = evaluate(persistence, make_entry(2, 10, stage=EmergingStage.BUILDING), kind=ExpectationKind.STAGE_PERSISTENCE, subject="stage", at=NOW + timedelta(minutes=10))
        self.assertIs(fulfilled.status, ExpectationEvaluationStatus.FULFILLED)
        self.assertIs(contradicted.status, ExpectationEvaluationStatus.CONTRADICTED)

    def test_invalidation_fulfilled_and_contradicted(self):
        invalidation = contract(
            rule_name="invalidation_risk", kind=ExpectationKind.INVALIDATION_RISK,
            subject="situation_viability", maturity_threshold=70.0,
            horizon_threshold=30.0, concentration_threshold=1,
            strengthening_thresholds={
                "minimum_emergence_increase": 10.0,
                "minimum_horizon_increase": 10.0,
                "minimum_supporting_factor_count": 2,
            },
            weakening_thresholds={
                "material_change_threshold": 20.0,
                "sharp_change_threshold": 35.0,
            },
        )
        exhausted = evaluate(invalidation, make_entry(2, 10, stage=EmergingStage.EXHAUSTED, dna=make_dna(maturity=80, horizon=20)), kind=ExpectationKind.INVALIDATION_RISK, subject="situation_viability", at=NOW + timedelta(minutes=10))
        stronger = evaluate(invalidation, make_entry(2, 10, dna=make_dna(emergence=80, horizon=95), supporting=("structure_event", "whale_activity", "volume_expansion")), kind=ExpectationKind.INVALIDATION_RISK, subject="situation_viability", at=NOW + timedelta(minutes=10))
        self.assertIs(exhausted.status, ExpectationEvaluationStatus.FULFILLED)
        self.assertIs(stronger.status, ExpectationEvaluationStatus.CONTRADICTED)


class UncertaintySurpriseAndFormattingTests(unittest.TestCase):
    def test_absent_contract_open_pending_closed_indeterminate_or_expired(self):
        historical = expectation_for(None)
        evidence = make_entry(2, 10)
        evaluator = SituationExpectationEvaluator()
        pending = evaluator.evaluate(historical, make_timeline(evidence), evaluated_at=NOW + timedelta(minutes=10))
        indeterminate = evaluator.evaluate(historical, make_timeline(evidence, updated_at=NOW + timedelta(minutes=61)), evaluated_at=NOW + timedelta(minutes=61))
        expired = evaluator.evaluate(historical, make_timeline(updated_at=NOW + timedelta(minutes=61)), evaluated_at=NOW + timedelta(minutes=61))
        self.assertIs(pending.status, ExpectationEvaluationStatus.PENDING)
        self.assertIs(indeterminate.status, ExpectationEvaluationStatus.INDETERMINATE)
        self.assertIs(expired.status, ExpectationEvaluationStatus.EXPIRED)
        self.assertIn("absent", indeterminate.metadata["contract_error"])

    def test_incomplete_contract_never_uses_current_policy_defaults(self):
        incomplete = volume_contract()
        del incomplete["confirmation_threshold"]
        result = evaluate(incomplete, make_entry(2, 10, dna=make_dna(volume_expansion=100)))
        self.assertIs(result.status, ExpectationEvaluationStatus.INDETERMINATE)
        self.assertFalse(result.fulfilled_criteria)

    def test_missing_data_is_not_missing_and_coverage_is_required(self):
        unavailable = make_dna(factor_availability=dict(make_dna().factor_availability, volume_expansion="MISSING"))
        mixed = evaluate(
            volume_contract(minimum_coverage_ratio=0.75),
            make_entry(2, 10, dna=make_dna(volume_expansion=20)),
            make_entry(3, 20, dna=unavailable),
        )
        self.assertIs(mixed.status, ExpectationEvaluationStatus.EXPIRED)

    def test_conflicting_fulfillment_and_contradiction_is_indeterminate(self):
        entry = make_entry(2, 10, dna=make_dna(volume_expansion=50, structure_event=10))
        result = evaluate(volume_contract(), entry, at=NOW + timedelta(minutes=10))
        self.assertIs(result.status, ExpectationEvaluationStatus.INDETERMINATE)

    def test_unexpected_factor_appearance_stage_jump_and_factor_loss(self):
        availability = dict(make_dna().factor_availability)
        availability["funding_divergence"] = "AVAILABLE"
        availability["whale_activity"] = "MISSING"
        dna = make_dna(
            funding_divergence=50,
            factor_availability=availability,
        )
        result = evaluate(
            volume_contract(),
            make_entry(2, 10, stage=EmergingStage.MATURE, dna=dna),
            at=NOW + timedelta(minutes=10),
        )
        rendered = " ".join(result.unexpected_events)
        self.assertIn("funding_divergence", rendered)
        self.assertIn("more than one", rendered)
        self.assertIn("whale_activity", rendered)

    def test_surprise_ranges_and_gap_mapping(self):
        fulfilled = evaluate(volume_contract(), make_entry(2, 10, dna=make_dna(volume_expansion=40)), at=NOW + timedelta(minutes=10))
        missing = evaluate(volume_contract(), make_entry(2, 10, dna=make_dna(volume_expansion=25)))
        contradicted = evaluate(volume_contract(), make_entry(2, 10, dna=make_dna(volume_expansion=25, structure_event=10)), at=NOW + timedelta(minutes=10))
        unavailable = make_dna(factor_availability=dict(make_dna().factor_availability, volume_expansion="MISSING"))
        expired = evaluate(volume_contract(), make_entry(2, 10, dna=unavailable))
        self.assertLessEqual(fulfilled.surprise_score, 20)
        self.assertGreaterEqual(missing.surprise_score, 50)
        self.assertGreaterEqual(contradicted.surprise_score, 70)
        self.assertEqual(25, expired.surprise_score)
        self.assertIs(fulfilled.gap_type, RealityGapType.NONE)
        self.assertIs(missing.gap_type, RealityGapType.MISSING_EXPECTED_EVENT)
        self.assertIs(contradicted.gap_type, RealityGapType.CONTRADICTORY_EVENT)
        self.assertIs(expired.gap_type, RealityGapType.UNKNOWN)

    def test_policy_is_frozen_and_validated(self):
        policy = ExpectationEvaluationPolicy()
        with self.assertRaises(FrozenInstanceError):
            policy.minimum_later_entries = 2
        with self.assertRaises(ValueError):
            ExpectationEvaluationPolicy(sufficient_coverage_ratio=1.1)

    def test_formatter_and_collection_formatter(self):
        result = evaluate(volume_contract(), make_entry(2, 10, dna=make_dna(volume_expansion=25)))
        rendered = format_expectation_evaluation(result)
        self.assertIn("SOL", rendered)
        self.assertIn("Status:\nMISSING", rendered)
        self.assertIn("What did not happen", rendered)
        self.assertNotIn("BUY", rendered.upper())
        self.assertIn(rendered, format_expectation_evaluations((result,)))
        self.assertEqual("No expectation evaluations.", format_expectation_evaluations(()))


class BoundaryTests(unittest.TestCase):
    def test_runtime_dependency_boundary_and_no_side_effect_imports(self):
        path = Path("app/intelligence/timeline/expectation_evaluation.py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        forbidden = ("telegram", "scanner", "provider", "exchange", "database",
                     "repository", "pipeline", "market_state", "experts", "learning")
        self.assertFalse(tuple(name for name in imports if any(item in name.lower() for item in forbidden)))
        source = path.read_text(encoding="utf-8")
        self.assertNotIn("open(", source)
        self.assertNotIn("requests", source)

    def test_demo_is_import_safe(self):
        module = importlib.import_module("run_expectation_evaluation_demo")
        self.assertTrue(callable(module.main))

    def test_demo_helper_uses_fake_wait_and_real_timestamps(self):
        class FakeSource:
            def source_name(self):
                return "fake-public-candles"

            def get_candles(self, asset, interval, start_time, end_time=None, limit=1000):
                del interval, start_time, end_time
                values = []
                for index in range(limit):
                    price = 100.0 + len(asset) + index * 0.01
                    values.append(Candle(
                        timestamp=NOW - timedelta(minutes=15 * (limit - index)),
                        open=price,
                        high=price * 1.01,
                        low=price * 0.99,
                        close=price,
                        volume=100.0 if index < limit - 1 else 300.0,
                    ))
                return values

        class FakeScanner:
            def __init__(self):
                self.calls = 0
                self.scanner = EarlyBirdScanner(candle_source=FakeSource())

            def scan(self, assets, timeframe="15m", limit=5):
                timestamp = NOW + timedelta(minutes=15 * self.calls)
                self.calls += 1
                return self.scanner.scan(
                    assets, timeframe=timeframe, limit=limit, timestamp=timestamp
                )

        waits = []
        first, second, evolution, expectations, evaluations = (
            run_two_scan_expectation_evaluation(
                scanner=FakeScanner(),
                assets=("BTC", "ETH"),
                limit=2,
                interval_seconds=60,
                sleep_fn=waits.append,
            )
        )
        self.assertEqual([60.0], waits)
        self.assertLess(first.started_at, second.started_at)
        self.assertEqual(2, len(evolution.decisions))
        self.assertTrue(expectations)
        self.assertTrue(evaluations)
        self.assertTrue(all(item.evaluated_at == second.started_at for item in evaluations))

    def test_arbitrary_presentation_text_is_not_parsed(self):
        expectation = expectation_for(
            volume_contract(),
            fulfillment_criteria=("BUY SELL 999 arbitrary text",),
            contradiction_criteria=("unparseable prose",),
        )
        entry = make_entry(2, 10, dna=make_dna(volume_expansion=40))
        result = SituationExpectationEvaluator().evaluate(
            expectation, make_timeline(entry), evaluated_at=entry.created_at
        )
        self.assertIs(result.status, ExpectationEvaluationStatus.FULFILLED)


if __name__ == "__main__":
    unittest.main()
