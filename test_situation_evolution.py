"""Focused offline tests for PS-4 Step 4 Situation evolution."""

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
    DeltaState,
    EvolutionAction,
    MarketSituationTimeline,
    MarketSituationTimelineEntry,
    SituationDNA,
    SituationDNADelta,
    SituationEvolutionBatchResult,
    SituationEvolutionDecision,
    SituationEvolutionEngine,
    extract_situation_dna_deltas,
    format_situation_evolution,
    format_situation_evolution_batch,
)
from run_early_bird_evolution_demo import run_two_scan_evolution


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
        "metadata": {"source": "fixture"},
    }
    values.update(overrides)
    return SituationDNA(**values)


def make_entry(
    timeline_id,
    entry_id,
    at,
    stage=EmergingStage.EMERGING,
    dna=None,
    supporting=("volume_expansion", "structure_event"),
    limiting=("whale_activity",),
):
    return MarketSituationTimelineEntry(
        entry_id=entry_id,
        timeline_id=timeline_id,
        created_at=at,
        stage=stage,
        dna=dna or make_dna(),
        supporting_factors=supporting,
        limiting_factors=limiting,
        expected_events=("volume_follow_through",),
        observed_events=("measured_factor:volume_expansion",),
        missing_expected_events=(),
        unexpected_events=(),
        transition_reason="Point-in-time fixture stage recorded.",
        source_assessment_id="assessment-{0}".format(entry_id),
        source_candidate_id="candidate-{0}".format(entry_id),
        source_situation_id=None,
        metadata={"source": "fixture"},
    )


def make_timeline(
    timeline_id="existing-link",
    asset="LINK",
    at=NOW,
    stage=EmergingStage.EMERGING,
    version=1,
    dna=None,
    entry_id=None,
    supporting=("volume_expansion", "structure_event"),
    limiting=("whale_activity",),
    metadata=None,
):
    entry = make_entry(
        timeline_id,
        entry_id or "entry-{0}".format(timeline_id),
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
    at=NOW + timedelta(minutes=15),
    stage=EmergingStage.BUILDING,
    dna=None,
    timeline_id=None,
    entry_id=None,
    version=1,
    supporting=("volume_expansion", "structure_event"),
    limiting=("whale_activity",),
):
    normalized = asset.upper()
    return make_timeline(
        timeline_id=timeline_id or "candidate-{0}".format(normalized.lower()),
        asset=normalized,
        at=at,
        stage=stage,
        dna=dna,
        entry_id=entry_id,
        version=version,
        supporting=supporting,
        limiting=limiting,
    )


def evolve(existing=None, candidates=None, **kwargs):
    return SituationEvolutionEngine().evolve(
        existing_timelines={} if existing is None else existing,
        candidate_timelines=(make_candidate(),) if candidates is None else candidates,
        updated_at=kwargs.pop("updated_at", NOW + timedelta(minutes=15)),
        first_scan_at=kwargs.pop("first_scan_at", NOW),
        **kwargs
    )


class EvolutionBehaviorTests(unittest.TestCase):
    def test_no_existing_timeline_creates_new(self):
        result = evolve()
        decision = result.decisions[0]
        self.assertIs(decision.action, EvolutionAction.CREATED)
        self.assertEqual(1, decision.result_version)
        self.assertFalse(decision.identity_result.matched)
        self.assertFalse(decision.identity_result.metadata["evaluation_performed"])

    def test_matching_identity_continues_timeline(self):
        existing = make_timeline()
        result = evolve({"LINK": existing})
        decision = result.decisions[0]
        self.assertIs(decision.action, EvolutionAction.CONTINUED)
        self.assertTrue(decision.identity_result.matched)
        self.assertEqual(existing.timeline_id, decision.result_timeline_id)

    def test_unmatched_identity_creates_new_and_preserves_provenance(self):
        existing = make_timeline(stage=EmergingStage.EXHAUSTED)
        candidate = make_candidate()
        result = evolve({"LINK": existing}, (candidate,))
        decision = result.decisions[0]
        self.assertIs(decision.action, EvolutionAction.CREATED)
        self.assertEqual(candidate.timeline_id, result.active_timelines["LINK"].timeline_id)
        self.assertEqual(existing.timeline_id, decision.previous_timeline_id)
        self.assertEqual("existing_timeline_exhausted", decision.identity_result.metadata["rejection_code"])

    def test_continuation_increments_exactly_once(self):
        existing = make_timeline(version=7)
        result = evolve({"LINK": existing})
        self.assertEqual(8, result.active_timelines["LINK"].version)
        self.assertEqual(8, result.decisions[0].result_version)

    def test_new_timeline_remains_version_one(self):
        result = evolve()
        self.assertEqual(1, result.active_timelines["LINK"].version)

    def test_existing_and_candidate_remain_unchanged(self):
        existing = make_timeline()
        candidate = make_candidate()
        existing_payload = existing.to_dict()
        candidate_payload = candidate.to_dict()
        result = evolve({"LINK": existing}, (candidate,))
        self.assertEqual(existing_payload, existing.to_dict())
        self.assertEqual(candidate_payload, candidate.to_dict())
        self.assertIsNot(existing, result.active_timelines["LINK"])

    def test_previous_entries_preserved_and_candidate_appended_once(self):
        existing = make_timeline()
        candidate = make_candidate()
        timeline = evolve({"LINK": existing}, (candidate,)).active_timelines["LINK"]
        self.assertEqual(2, len(timeline.entries))
        self.assertIs(existing.entries[0], timeline.entries[0])
        self.assertEqual(candidate.entries[0].entry_id, timeline.entries[1].entry_id)

    def test_continuation_preserves_timeline_and_source_ids(self):
        existing = make_timeline()
        candidate = make_candidate()
        timeline = evolve({"LINK": existing}, (candidate,)).active_timelines["LINK"]
        appended = timeline.entries[-1]
        self.assertEqual(existing.timeline_id, appended.timeline_id)
        self.assertEqual(candidate.entries[0].source_assessment_id, appended.source_assessment_id)
        self.assertEqual(candidate.entries[0].source_candidate_id, appended.source_candidate_id)
        self.assertIs(candidate.entries[0].dna, appended.dna)

    def test_point_in_time_entry_facts_are_preserved(self):
        existing = make_timeline()
        candidate = make_candidate()
        appended = evolve({"LINK": existing}, (candidate,)).active_timelines["LINK"].entries[-1]
        source = candidate.entries[0]
        self.assertEqual(source.created_at, appended.created_at)
        self.assertEqual(source.expected_events, appended.expected_events)
        self.assertEqual(source.observed_events, appended.observed_events)
        self.assertEqual(source.transition_reason, appended.transition_reason)
        self.assertIn("identity_provenance", appended.metadata)

    def test_stage_change_same_stage_and_regression_are_descriptive(self):
        existing = make_timeline(stage=EmergingStage.BUILDING)
        changed = evolve(
            {"LINK": existing},
            (make_candidate(stage=EmergingStage.MATURE),),
        ).decisions[0]
        same = evolve(
            {"LINK": existing},
            (make_candidate(stage=EmergingStage.BUILDING),),
        ).decisions[0]
        regressed = evolve(
            {"LINK": existing},
            (make_candidate(stage=EmergingStage.EMERGING),),
        ).decisions[0]
        self.assertTrue(changed.stage_changed)
        self.assertFalse(same.stage_changed)
        self.assertTrue(regressed.stage_changed)
        self.assertIs(regressed.new_stage, EmergingStage.EMERGING)

    def test_identity_trace_and_hard_rejection_are_preserved(self):
        matched = evolve({"LINK": make_timeline()}).decisions[0]
        trace = matched.metadata["identity_trace"]
        self.assertIn("criteria", trace["metadata"])
        self.assertIn("match_threshold", trace["metadata"])
        self.assertIn("time_gap_seconds", trace["metadata"])
        self.assertEqual(1, trace["metadata"]["identity_policy_version"])
        rejected = evolve(
            {"LINK": make_timeline(stage=EmergingStage.EXHAUSTED)}
        ).decisions[0]
        self.assertTrue(rejected.identity_result.metadata["hard_rejection"])

    def test_one_asset_failure_does_not_abort_batch(self):
        bad = make_candidate(asset="LINK", entry_id="entry-existing-link")
        good = make_candidate(asset="ETH")
        result = evolve(
            {"LINK": make_timeline()},
            (bad, good),
        )
        self.assertIn("LINK", result.errors)
        self.assertEqual(("ETH",), tuple(item.asset for item in result.decisions))
        self.assertIn("ETH", result.active_timelines)

    def test_deterministic_order_and_duplicate_candidate_rejection(self):
        eth = make_candidate(asset="ETH")
        link = make_candidate(asset="LINK")
        result = evolve(candidates=(link, eth))
        self.assertEqual(("ETH", "LINK"), tuple(item.asset for item in result.decisions))
        duplicate = evolve(candidates=(link, make_candidate(asset="LINK", timeline_id="other")))
        self.assertEqual((), duplicate.decisions)
        self.assertIn("duplicate candidate asset", duplicate.errors["LINK"])

    def test_invalid_candidate_version_and_entry_count_are_isolated(self):
        version_two = make_candidate(version=2)
        empty = MarketSituationTimeline(
            timeline_id="candidate-empty",
            asset="ETH",
            created_at=NOW,
            updated_at=NOW,
            entries=(),
            current_stage=EmergingStage.UNKNOWN,
            version=1,
            metadata={},
        )
        result = evolve(candidates=(version_two, empty))
        self.assertIn("LINK", result.errors)
        self.assertIn("ETH", result.errors)
        self.assertEqual((), result.decisions)

    def test_updated_at_requires_aware_utc_and_normalizes(self):
        with self.assertRaises(ValueError):
            evolve(updated_at=NOW.replace(tzinfo=None))
        offset = timezone(timedelta(hours=2))
        result = evolve(updated_at=(NOW + timedelta(minutes=15)).astimezone(offset))
        self.assertIs(result.second_scan_at.tzinfo, UTC)


class DeltaTests(unittest.TestCase):
    def delta(self, previous, current, field_name):
        return next(
            item
            for item in extract_situation_dna_deltas(previous, current)
            if item.field_name == field_name
        )

    def test_measured_to_measured_delta_and_zero(self):
        previous = make_dna(volume_expansion=0)
        current = make_dna(volume_expansion=25)
        delta = self.delta(previous, current, "volume_expansion")
        self.assertIs(delta.state, DeltaState.CHANGED)
        self.assertEqual(25.0, delta.numeric_delta)
        self.assertEqual(0.0, delta.previous_value)

    def test_none_to_measured_appeared(self):
        availability = dict(make_dna().factor_availability)
        availability["whale_activity"] = "AVAILABLE"
        delta = self.delta(
            make_dna(whale_activity=None),
            make_dna(whale_activity=70, factor_availability=availability),
            "whale_activity",
        )
        self.assertIs(delta.state, DeltaState.APPEARED)
        self.assertIsNone(delta.numeric_delta)

    def test_measured_to_none_became_unavailable(self):
        previous_availability = dict(make_dna().factor_availability)
        previous_availability["whale_activity"] = "AVAILABLE"
        delta = self.delta(
            make_dna(whale_activity=70, factor_availability=previous_availability),
            make_dna(whale_activity=None),
            "whale_activity",
        )
        self.assertIs(delta.state, DeltaState.BECAME_UNAVAILABLE)

    def test_availability_change_is_separate(self):
        previous_availability = dict(make_dna().factor_availability)
        current_availability = dict(previous_availability)
        previous_availability["whale_activity"] = "MISSING"
        current_availability["whale_activity"] = "ERROR"
        delta = self.delta(
            make_dna(factor_availability=previous_availability),
            make_dna(factor_availability=current_availability),
            "whale_activity",
        )
        self.assertIs(delta.state, DeltaState.UNCHANGED)
        self.assertTrue(delta.availability_changed)
        self.assertTrue(delta.material)

    def test_all_fields_have_deterministic_order_and_round_trip(self):
        deltas = extract_situation_dna_deltas(make_dna(), make_dna())
        self.assertEqual(17, len(deltas))
        self.assertEqual("whale_activity", deltas[0].field_name)
        self.assertEqual("detection_confidence", deltas[-1].field_name)
        self.assertEqual(deltas[0], SituationDNADelta.from_dict(deltas[0].to_dict()))


class ModelAndFormatterTests(unittest.TestCase):
    def test_batch_and_decision_are_immutable_and_deeply_frozen(self):
        result = evolve({"LINK": make_timeline()})
        decision = result.decisions[0]
        self.assertIsInstance(result.active_timelines, MappingProxyType)
        self.assertIsInstance(result.errors, MappingProxyType)
        self.assertIsInstance(decision.metadata, MappingProxyType)
        with self.assertRaises(FrozenInstanceError):
            decision.action = EvolutionAction.CREATED
        with self.assertRaises(TypeError):
            result.active_timelines["ETH"] = make_candidate(asset="ETH")

    def test_serialization_round_trip(self):
        result = evolve({"LINK": make_timeline()})
        restored = SituationEvolutionBatchResult.from_dict(result.to_dict())
        self.assertEqual(result, restored)
        decision = result.decisions[0]
        self.assertEqual(decision, SituationEvolutionDecision.from_dict(decision.to_dict()))

    def test_models_have_no_trade_fields(self):
        names = {item.name for item in fields(SituationEvolutionDecision)}
        self.assertFalse(names & {"trade", "direction", "recommendation", "buy", "sell", "execution"})

    def test_formatter_outputs_decision_trace_and_deltas(self):
        previous = make_timeline(dna=make_dna(volume_expansion=32, horizon=74))
        candidate = make_candidate(dna=make_dna(volume_expansion=58, horizon=55))
        decision = evolve({"LINK": previous}, (candidate,)).decisions[0]
        text = format_situation_evolution(decision)
        self.assertIn("Action: CONTINUED", text)
        self.assertIn("Version: 1 -> 2", text)
        self.assertIn("Volume Expansion: 32 -> 58", text)
        self.assertIn("Horizon: 74 -> 55", text)
        self.assertIn("Identity confidence", text)
        self.assertNotIn("BUY", text.upper())
        batch_text = format_situation_evolution_batch(evolve({"LINK": previous}, (candidate,)))
        self.assertIn("Created: 0", batch_text)
        self.assertIn("Continued: 1", batch_text)


class FakeCandleSource:
    def source_name(self):
        return "fake-public-candles"

    def get_candles(self, asset, interval, start_time, end_time=None, limit=1000):
        del interval, start_time, end_time
        base = 100.0 + len(asset)
        completed_at = NOW - timedelta(minutes=15)
        values = []
        for index in range(limit):
            price = base + index * 0.01
            values.append(
                Candle(
                    timestamp=completed_at - timedelta(minutes=15 * (limit - index)),
                    open=price,
                    high=price * 1.01,
                    low=price * 0.99,
                    close=price,
                    volume=100.0 if index < limit - 1 else 300.0,
                )
            )
        return values


class FakeScanner:
    def __init__(self):
        self.calls = 0
        self.scanner = EarlyBirdScanner(candle_source=FakeCandleSource())

    def scan(self, assets, timeframe="15m", limit=5):
        timestamp = NOW + timedelta(minutes=15 * self.calls)
        self.calls += 1
        return self.scanner.scan(
            assets,
            timeframe=timeframe,
            limit=limit,
            timestamp=timestamp,
        )


class OrchestrationAndBoundaryTests(unittest.TestCase):
    def test_two_scan_helper_uses_fake_wait_and_returns_evolution(self):
        waits = []
        first, second, result = run_two_scan_evolution(
            scanner=FakeScanner(),
            assets=("BTC", "ETH"),
            limit=2,
            interval_seconds=60,
            sleep_fn=waits.append,
        )
        self.assertEqual([60.0], waits)
        self.assertLess(first.started_at, second.started_at)
        self.assertEqual(2, len(result.decisions))
        self.assertFalse(result.errors)

    def test_demo_is_import_safe(self):
        module = importlib.import_module("run_early_bird_evolution_demo")
        self.assertTrue(callable(module.main))

    def test_runtime_dependency_boundary(self):
        source = Path("app/intelligence/timeline/evolution.py").read_text()
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        forbidden = (
            "telegram",
            "database",
            "repository",
            "pipeline",
            "provider",
            "exchange",
            "network",
            "market_state",
            "experts",
            "decision",
            "trade_readiness",
        )
        self.assertFalse(
            [name for name in imports if any(part in name.lower() for part in forbidden)]
        )

    def test_demo_has_no_import_time_execution_or_write_calls(self):
        source = Path("run_early_bird_evolution_demo.py").read_text()
        tree = ast.parse(source)
        top_level_calls = [
            node
            for node in tree.body
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        ]
        self.assertEqual([], top_level_calls)
        self.assertNotIn("open(", source)
        self.assertNotIn("Path(", source)


if __name__ == "__main__":
    unittest.main()
