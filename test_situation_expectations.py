"""Focused offline tests for the PS-4 Step 5 Expectation Engine."""

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
    ExpectationKind,
    ExpectationPolicy,
    ExpectationStrength,
    MarketSituationTimeline,
    MarketSituationTimelineEntry,
    SituationDNA,
    SituationExpectation,
    SituationExpectationEngine,
    deterministic_expectation_id,
    format_situation_expectation,
    format_situation_expectations,
)
from run_situation_expectation_demo import generate_scan_expectations


UTC = timezone.utc
NOW = datetime(2026, 7, 15, 15, 0, tzinfo=UTC)
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


def available_map(**overrides):
    values = {name: "AVAILABLE" for name in FACTORS}
    values.update(overrides)
    return values


def make_dna(**overrides):
    values = {
        "whale_activity": 10.0,
        "funding_divergence": 10.0,
        "volume_expansion": 20.0,
        "structure_event": 55.0,
        "momentum_shift": 20.0,
        "relative_strength": 50.0,
        "open_interest_change": 15.0,
        "liquidity_event": 10.0,
        "completeness": 100.0,
        "quality": 80.0,
        "freshness": 90.0,
        "opportunity": 60.0,
        "priority": 65.0,
        "maturity": 30.0,
        "emergence": 65.0,
        "horizon": 80.0,
        "detection_confidence": 72.0,
        "factor_availability": available_map(),
        "metadata": {"source": "fixture"},
    }
    values.update(overrides)
    return SituationDNA(**values)


def make_timeline(
    *,
    asset="near",
    timeline_id="timeline-near",
    version=3,
    stage=EmergingStage.EMERGING,
    dna=None,
    at=NOW,
    supporting=("structure_event", "volume_expansion"),
):
    entry = MarketSituationTimelineEntry(
        entry_id="entry-near-v{0}".format(version),
        timeline_id=timeline_id,
        created_at=at,
        stage=stage,
        dna=dna or make_dna(),
        supporting_factors=supporting,
        limiting_factors=(),
        expected_events=(),
        observed_events=("fixture:measured",),
        missing_expected_events=(),
        unexpected_events=(),
        transition_reason="Fixture state recorded.",
        source_assessment_id="assessment-near",
        source_candidate_id="candidate-near",
        source_situation_id=None,
        metadata={},
    )
    return MarketSituationTimeline(
        timeline_id=timeline_id,
        asset=asset,
        created_at=at,
        updated_at=at,
        entries=(entry,),
        current_stage=stage,
        version=version,
        metadata={},
    )


def make_expectation(**overrides):
    values = {
        "expectation_id": "expectation:fixture",
        "timeline_id": "timeline-near",
        "timeline_version": 3,
        "asset": "near",
        "created_at": NOW,
        "window_start": NOW,
        "window_end": NOW + timedelta(hours=1),
        "kind": ExpectationKind.CONFIRMATION,
        "strength": ExpectationStrength.MEDIUM,
        "subject": "volume_expansion",
        "description": "Future measured volume confirmation is expected.",
        "basis": ("structure_event=55 AVAILABLE",),
        "fulfillment_criteria": ("Volume Expansion becomes measured above 35.",),
        "contradiction_criteria": ("The window expires without confirmation.",),
        "source_entry_id": "entry-near-v3",
        "source_stage": EmergingStage.EMERGING,
        "source_factor_values": {
            "whale_activity": 10.0,
            "funding_divergence": None,
            "volume_expansion": 20.0,
            "structure_event": 55.0,
            "momentum_shift": 20.0,
            "relative_strength": 50.0,
            "open_interest_change": None,
            "liquidity_event": None,
        },
        "source_factor_availability": available_map(
            funding_divergence="MISSING",
            open_interest_change="UNSUPPORTED",
            liquidity_event="ERROR",
        ),
        "metadata": {"policy_version": 1, "nested": {"facts": [1, 2]}},
    }
    values.update(overrides)
    return SituationExpectation(**values)


def by_rule(expectations, rule_name):
    return tuple(
        item for item in expectations if item.metadata["rule_name"] == rule_name
    )


class ExpectationModelTests(unittest.TestCase):
    def test_valid_expectation_and_asset_normalization(self):
        expectation = make_expectation()
        self.assertEqual("NEAR", expectation.asset)
        self.assertIs(expectation.kind, ExpectationKind.CONFIRMATION)

    def test_immutable_and_deeply_frozen(self):
        expectation = make_expectation()
        self.assertIsInstance(expectation.metadata, MappingProxyType)
        self.assertIsInstance(expectation.metadata["nested"], MappingProxyType)
        self.assertIsInstance(expectation.metadata["nested"]["facts"], tuple)
        with self.assertRaises(FrozenInstanceError):
            expectation.asset = "ETH"
        with self.assertRaises(TypeError):
            expectation.metadata["x"] = 1

    def test_serialization_round_trip(self):
        expectation = make_expectation()
        self.assertEqual(
            expectation,
            SituationExpectation.from_dict(expectation.to_dict()),
        )

    def test_naive_timestamp_rejected_and_aware_normalized(self):
        with self.assertRaises(ValueError):
            make_expectation(created_at=NOW.replace(tzinfo=None))
        offset = timezone(timedelta(hours=2))
        expectation = make_expectation(created_at=NOW.astimezone(offset))
        self.assertIs(expectation.created_at.tzinfo, UTC)

    def test_invalid_window_rejected(self):
        with self.assertRaises(ValueError):
            make_expectation(window_start=NOW - timedelta(seconds=1))
        with self.assertRaises(ValueError):
            make_expectation(window_end=NOW - timedelta(seconds=1))

    def test_explicit_collections_must_not_be_empty(self):
        for name in ("basis", "fulfillment_criteria", "contradiction_criteria"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                make_expectation(**{name: ()})

    def test_no_evaluation_outcome_or_trade_fields(self):
        names = {item.name for item in fields(SituationExpectation)}
        self.assertFalse(
            names
            & {
                "evaluation_status",
                "status",
                "observed_outcome",
                "outcome",
                "direction",
                "buy",
                "sell",
                "long",
                "short",
                "tp",
                "sl",
                "trade_entry",
            }
        )

    def test_source_factor_values_and_availability_preserved(self):
        expectation = make_expectation()
        self.assertEqual(20.0, expectation.source_factor_values["volume_expansion"])
        self.assertIsNone(expectation.source_factor_values["funding_divergence"])
        self.assertEqual("MISSING", expectation.source_factor_availability["funding_divergence"])

    def test_measured_zero_is_preserved(self):
        values = dict(make_expectation().source_factor_values)
        values["volume_expansion"] = 0
        expectation = make_expectation(source_factor_values=values)
        self.assertEqual(0.0, expectation.source_factor_values["volume_expansion"])

    def test_availability_value_consistency_is_enforced(self):
        values = dict(make_expectation().source_factor_values)
        values["funding_divergence"] = 0
        with self.assertRaises(ValueError):
            make_expectation(source_factor_values=values)
        availability = dict(make_expectation().source_factor_availability)
        availability["volume_expansion"] = "MISSING"
        with self.assertRaises(ValueError):
            make_expectation(source_factor_availability=availability)

    def test_source_timeline_version_and_entry_preserved(self):
        expectation = make_expectation()
        self.assertEqual(3, expectation.timeline_version)
        self.assertEqual("entry-near-v3", expectation.source_entry_id)


class PolicyAndDeterminismTests(unittest.TestCase):
    def test_policy_defaults_and_immutability(self):
        policy = ExpectationPolicy()
        self.assertEqual(60, policy.default_window_minutes)
        self.assertEqual(5, policy.maximum_expectations)
        with self.assertRaises(FrozenInstanceError):
            policy.policy_version = 2

    def test_policy_validation(self):
        with self.assertRaises(ValueError):
            ExpectationPolicy(short_window_minutes=90)
        with self.assertRaises(ValueError):
            ExpectationPolicy(material_factor_threshold=70, strong_factor_threshold=60)

    def test_deterministic_ids_and_identical_input(self):
        timeline = make_timeline()
        engine = SituationExpectationEngine()
        first = engine.generate(timeline)
        second = engine.generate(timeline)
        self.assertEqual(first, second)
        self.assertEqual(
            "expectation:timeline-near:v3:volume_confirmation:volume_expansion",
            deterministic_expectation_id(timeline, "volume_confirmation", "volume_expansion"),
        )

    def test_deterministic_rule_then_subject_order(self):
        dna = make_dna(
            whale_activity=80,
            funding_divergence=70,
            structure_event=65,
            volume_expansion=65,
            momentum_shift=50,
        )
        expectations = SituationExpectationEngine(
            ExpectationPolicy(maximum_expectations=10)
        ).generate(make_timeline(dna=dna))
        rules = tuple(item.metadata["rule_name"] for item in expectations)
        self.assertEqual(
            (
                "factor_persistence",
                "factor_persistence",
                "factor_persistence",
                "factor_persistence",
                "stage_advance_emerging_to_building",
            ),
            rules,
        )
        persistence_subjects = tuple(
            item.subject
            for item in expectations
            if item.kind is ExpectationKind.FACTOR_PERSISTENCE
        )
        self.assertEqual(tuple(sorted(persistence_subjects)), persistence_subjects)

    def test_maximum_expectation_limit_applied_after_order(self):
        dna = make_dna(
            whale_activity=80,
            funding_divergence=70,
            structure_event=65,
            volume_expansion=65,
            momentum_shift=50,
        )
        expectations = SituationExpectationEngine(
            ExpectationPolicy(maximum_expectations=2)
        ).generate(make_timeline(dna=dna))
        self.assertEqual(2, len(expectations))
        self.assertTrue(all(item.kind is ExpectationKind.FACTOR_PERSISTENCE for item in expectations))

    def test_no_duplicate_expectations(self):
        expectations = SituationExpectationEngine().generate(make_timeline())
        ids = tuple(item.expectation_id for item in expectations)
        self.assertEqual(len(ids), len(set(ids)))


class EvaluationContractAmendmentTests(unittest.TestCase):
    def generated_by_rule(self):
        engine = SituationExpectationEngine(
            ExpectationPolicy(maximum_expectations=10)
        )
        values = []
        values.extend(engine.generate(make_timeline()))
        values.extend(engine.generate(make_timeline(
            dna=make_dna(
                whale_activity=75,
                funding_divergence=70,
                structure_event=65,
                volume_expansion=65,
                momentum_shift=50,
            )
        )))
        missing_funding = available_map(funding_divergence="MISSING")
        values.extend(engine.generate(make_timeline(
            dna=make_dna(
                funding_divergence=None,
                structure_event=70,
                volume_expansion=65,
                momentum_shift=50,
                factor_availability=missing_funding,
            )
        )))
        values.extend(engine.generate(make_timeline(
            dna=make_dna(emergence=40),
            stage=EmergingStage.BUILDING,
        )))
        return values

    def test_every_generated_rule_has_common_evaluation_contract(self):
        required = {
            "contract_version",
            "rule_name",
            "expectation_kind",
            "subject",
            "source_policy_version",
            "source_timeline_version",
            "source_stage",
            "window_minutes",
        }
        values = self.generated_by_rule()
        self.assertTrue(values)
        for expectation in values:
            with self.subTest(expectation=expectation.expectation_id):
                contract = expectation.metadata["evaluation_contract"]
                self.assertTrue(required <= set(contract))
                self.assertEqual("1", contract["contract_version"])
                self.assertEqual(expectation.metadata["rule_name"], contract["rule_name"])
                self.assertEqual(expectation.kind.value, contract["expectation_kind"])

    def test_rule_specific_required_parameters_are_present(self):
        required = {
            "volume_confirmation": {
                "target_factor", "confirmation_threshold",
                "structure_material_threshold", "structure_contradiction_threshold",
                "maturity_contradiction_threshold", "minimum_coverage_ratio",
            },
            "momentum_confirmation": {
                "target_factor", "confirmation_threshold", "initiating_factors",
                "initiating_factor_threshold", "contradiction_threshold",
                "minimum_coverage_ratio",
            },
            "factor_persistence": {
                "target_factor", "persistence_threshold", "contradiction_threshold",
                "minimum_required_later_entries",
            },
            "funding_appearance_after_structure_volume": {
                "target_factor", "source_required_availability",
                "fulfillment_availability", "missing_confirmation_availability",
                "disqualifying_availability_states", "minimum_required_later_entries",
            },
            "stage_persistence_building": {
                "source_stage", "required_stage", "minimum_required_later_entries",
            },
            "invalidation_risk": {
                "maturity_threshold", "horizon_threshold", "concentration_threshold",
                "strengthening_thresholds", "weakening_thresholds",
            },
        }
        contracts = {
            item.metadata["rule_name"]: item.metadata["evaluation_contract"]
            for item in self.generated_by_rule()
        }
        stage_advance = next(
            value for key, value in contracts.items()
            if key.startswith("stage_advance_")
        )
        self.assertTrue({
            "source_stage", "expected_target_stage", "incompatible_stages",
            "minimum_required_later_entries",
        } <= set(stage_advance))
        for rule_name, names in required.items():
            with self.subTest(rule_name=rule_name):
                self.assertTrue(names <= set(contracts[rule_name]))

    def test_evaluation_contract_is_deeply_immutable(self):
        expectation = SituationExpectationEngine().generate(make_timeline())[0]
        contract = expectation.metadata["evaluation_contract"]
        self.assertIsInstance(contract, MappingProxyType)
        with self.assertRaises(TypeError):
            contract["confirmation_threshold"] = 99

    def test_evaluation_contract_serialization_round_trip(self):
        expectation = SituationExpectationEngine().generate(make_timeline())[0]
        restored = SituationExpectation.from_dict(expectation.to_dict())
        self.assertEqual(expectation, restored)
        self.assertEqual(
            expectation.metadata["evaluation_contract"],
            restored.metadata["evaluation_contract"],
        )

    def test_historical_payload_without_evaluation_contract_still_loads(self):
        payload = make_expectation().to_dict()
        payload["metadata"].pop("evaluation_contract", None)
        restored = SituationExpectation.from_dict(payload)
        self.assertNotIn("evaluation_contract", restored.metadata)


class ExpectationRuleTests(unittest.TestCase):
    def generate(self, dna=None, stage=EmergingStage.EMERGING, supporting=("structure_event", "volume_expansion"), policy=None):
        return SituationExpectationEngine(policy).generate(
            make_timeline(dna=dna, stage=stage, supporting=supporting)
        )

    def test_empty_timeline_rejected(self):
        empty = MarketSituationTimeline(
            timeline_id="empty",
            asset="NEAR",
            created_at=NOW,
            updated_at=NOW,
            entries=(),
            current_stage=EmergingStage.UNKNOWN,
            version=1,
            metadata={},
        )
        with self.assertRaises(ValueError):
            SituationExpectationEngine().generate(empty)

    def test_created_at_before_latest_entry_rejected(self):
        with self.assertRaises(ValueError):
            SituationExpectationEngine().generate(
                make_timeline(),
                created_at=NOW - timedelta(seconds=1),
            )

    def test_volume_confirmation_generated_from_measured_weak_volume(self):
        expectations = self.generate()
        result = by_rule(expectations, "volume_confirmation")
        self.assertEqual(1, len(result))
        self.assertEqual("volume_expansion", result[0].subject)
        self.assertIn("volume_expansion=20 AVAILABLE", result[0].basis)

    def test_unavailable_volume_is_not_weak(self):
        availability = available_map(volume_expansion="MISSING")
        dna = make_dna(volume_expansion=None, factor_availability=availability)
        self.assertFalse(by_rule(self.generate(dna), "volume_confirmation"))

    def test_momentum_confirmation_generated(self):
        result = by_rule(self.generate(), "momentum_confirmation")
        self.assertEqual(1, len(result))
        self.assertEqual("momentum_shift", result[0].subject)

    def test_unavailable_momentum_is_not_weak(self):
        availability = available_map(momentum_shift="ERROR")
        dna = make_dna(momentum_shift=None, factor_availability=availability)
        self.assertFalse(by_rule(self.generate(dna), "momentum_confirmation"))

    def test_strong_factor_persistence_generated(self):
        expectations = self.generate(make_dna(whale_activity=75))
        matches = tuple(
            item for item in expectations
            if item.kind is ExpectationKind.FACTOR_PERSISTENCE
            and item.subject == "whale_activity"
        )
        self.assertEqual(1, len(matches))

    def test_missing_factor_not_used_for_persistence(self):
        availability = available_map(whale_activity="MISSING")
        dna = make_dna(whale_activity=None, factor_availability=availability)
        self.assertFalse(tuple(
            item for item in self.generate(dna)
            if item.kind is ExpectationKind.FACTOR_PERSISTENCE
            and item.subject == "whale_activity"
        ))

    def test_funding_appearance_only_under_approved_missing_rule(self):
        availability = available_map(funding_divergence="MISSING")
        dna = make_dna(
            funding_divergence=None,
            structure_event=70,
            volume_expansion=65,
            momentum_shift=50,
            factor_availability=availability,
        )
        matches = tuple(
            item for item in self.generate(dna)
            if item.kind is ExpectationKind.FACTOR_APPEARANCE
        )
        self.assertEqual(("funding_divergence",), tuple(item.subject for item in matches))

    def test_unsupported_funding_does_not_generate_appearance(self):
        availability = available_map(funding_divergence="UNSUPPORTED")
        dna = make_dna(
            funding_divergence=None,
            structure_event=70,
            volume_expansion=65,
            factor_availability=availability,
        )
        self.assertFalse(tuple(
            item for item in self.generate(dna)
            if item.kind is ExpectationKind.FACTOR_APPEARANCE
        ))

    def test_missing_whale_never_generates_whale_appearance(self):
        availability = available_map(whale_activity="MISSING")
        dna = make_dna(whale_activity=None, factor_availability=availability)
        self.assertFalse(tuple(
            item for item in self.generate(dna)
            if item.kind is ExpectationKind.FACTOR_APPEARANCE
            and item.subject == "whale_activity"
        ))

    def test_stage_advance_seed_to_emerging(self):
        result = tuple(
            item for item in self.generate(stage=EmergingStage.SEED)
            if item.kind is ExpectationKind.STAGE_ADVANCE
        )
        self.assertEqual(("EMERGING",), tuple(item.subject for item in result))

    def test_stage_advance_emerging_to_building(self):
        result = tuple(
            item for item in self.generate(stage=EmergingStage.EMERGING)
            if item.kind is ExpectationKind.STAGE_ADVANCE
        )
        self.assertEqual(("BUILDING",), tuple(item.subject for item in result))

    def test_no_stage_jump_or_advance_from_building(self):
        result = tuple(
            item for item in self.generate(stage=EmergingStage.BUILDING)
            if item.kind is ExpectationKind.STAGE_ADVANCE
        )
        self.assertEqual((), result)

    def test_stage_persistence_is_fallback_only(self):
        dna = make_dna(emergence=40)
        expectations = self.generate(dna, stage=EmergingStage.EMERGING)
        self.assertTrue(tuple(item for item in expectations if item.kind is ExpectationKind.STAGE_PERSISTENCE))
        advanced = self.generate(stage=EmergingStage.EMERGING)
        self.assertFalse(tuple(item for item in advanced if item.kind is ExpectationKind.STAGE_PERSISTENCE))

    def test_invalidation_risk_generated(self):
        dna = make_dna(maturity=80, horizon=20, emergence=40)
        result = tuple(
            item for item in self.generate(dna)
            if item.kind is ExpectationKind.INVALIDATION_RISK
        )
        self.assertEqual(1, len(result))
        self.assertIs(result[0].strength, ExpectationStrength.HIGH)

    def test_input_timeline_is_unchanged(self):
        timeline = make_timeline()
        before = timeline.to_dict()
        SituationExpectationEngine().generate(timeline)
        self.assertEqual(before, timeline.to_dict())

    def test_source_snapshot_matches_latest_entry(self):
        timeline = make_timeline(version=7)
        expectation = SituationExpectationEngine().generate(timeline)[0]
        self.assertEqual(7, expectation.timeline_version)
        self.assertEqual(timeline.entries[-1].entry_id, expectation.source_entry_id)
        self.assertEqual(timeline.entries[-1].dna.volume_expansion, expectation.source_factor_values["volume_expansion"])


class FormatterDemoAndBoundaryTests(unittest.TestCase):
    def test_formatter_output_is_unevaluated_and_non_trading(self):
        expectation = SituationExpectationEngine().generate(make_timeline())[0]
        text = format_situation_expectation(expectation)
        self.assertIn("Expectation: Volume Expansion confirmation", text)
        self.assertIn("Status:\n- NOT EVALUATED", text)
        self.assertIn("Contradicted if:", text)
        self.assertNotIn("BUY", text.upper())
        combined = format_situation_expectations((expectation,))
        self.assertEqual(text, combined)

    def test_demo_is_import_safe(self):
        module = importlib.import_module("run_situation_expectation_demo")
        self.assertTrue(callable(module.main))

    def test_runtime_dependency_boundary(self):
        source = Path("app/intelligence/timeline/expectations.py").read_text()
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        forbidden = (
            "scanner",
            "provider",
            "exchange",
            "network",
            "telegram",
            "database",
            "repository",
            "pipeline",
            "decision",
            "trade_readiness",
            "market_state",
            "experts",
            "outcome",
            "learning",
        )
        self.assertFalse([
            name for name in imports
            if any(part in name.lower() for part in forbidden)
        ])

    def test_demo_has_no_import_time_calls_or_disk_writes(self):
        source = Path("run_situation_expectation_demo.py").read_text()
        tree = ast.parse(source)
        top_level_calls = [
            node for node in tree.body
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        ]
        self.assertEqual([], top_level_calls)
        self.assertNotIn("open(", source)
        self.assertNotIn("Path(", source)

    def test_fake_scan_demo_helper_does_not_evaluate(self):
        class FakeSource:
            def source_name(self):
                return "fake-public-candles"

            def get_candles(self, asset, interval, start_time, end_time=None, limit=1000):
                del interval, start_time, end_time
                values = []
                for index in range(limit):
                    price = 100 + index * 0.01
                    values.append(Candle(
                        timestamp=NOW - timedelta(minutes=15 * (limit - index)),
                        open=price,
                        high=price * 1.01,
                        low=price * 0.99,
                        close=price,
                        volume=100 if index < limit - 1 else 300,
                    ))
                return values

        class FakeScanner:
            def scan(self, assets, timeframe="15m", limit=5):
                return EarlyBirdScanner(candle_source=FakeSource()).scan(
                    assets,
                    timeframe=timeframe,
                    limit=limit,
                    timestamp=NOW,
                )

        scan, timelines, generated = generate_scan_expectations(
            scanner=FakeScanner(),
            assets=("BTC", "ETH"),
            limit=2,
        )
        self.assertEqual(2, len(scan.items))
        self.assertEqual(2, len(timelines.results))
        self.assertEqual(2, len(generated))
        self.assertTrue(all(expectations for _, expectations in generated))
        self.assertFalse(any(
            "evaluation_status" in expectation.to_dict()
            for _, expectations in generated
            for expectation in expectations
        ))


if __name__ == "__main__":
    unittest.main()
