"""Focused tests for the PS-4 immutable Market Situation timeline."""

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import MappingProxyType
import unittest

from app.intelligence.early_bird import EmergingStage
from app.intelligence.timeline import (
    MarketSituationTimeline,
    MarketSituationTimelineEntry,
    SituationDNA,
    append_timeline_entry,
)


BASE_TIME = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)


def make_dna(**overrides):
    values = {
        "whale_activity": None,
        "funding_divergence": 62.0,
        "volume_expansion": 74.0,
        "structure_event": 41.0,
        "momentum_shift": 35.0,
        "relative_strength": 55.0,
        "open_interest_change": None,
        "liquidity_event": None,
        "completeness": 62.5,
        "quality": 78.0,
        "freshness": 91.0,
        "opportunity": 66.0,
        "priority": 73.0,
        "maturity": 24.0,
        "emergence": 81.0,
        "horizon": 88.0,
        "detection_confidence": 76.0,
        "factor_availability": {
            "funding_divergence": "AVAILABLE",
            "open_interest_change": "UNSUPPORTED",
            "whale_activity": "MISSING",
        },
        "metadata": {"window": {"minutes": 15}, "sources": ["candles"]},
    }
    values.update(overrides)
    return SituationDNA(**values)


def make_entry(
    entry_id="entry-1",
    stage=EmergingStage.SEED,
    created_at=BASE_TIME,
    timeline_id="timeline-1",
    **overrides
):
    values = {
        "entry_id": entry_id,
        "timeline_id": timeline_id,
        "created_at": created_at,
        "stage": stage,
        "dna": make_dna(),
        "supporting_factors": ("volume_expansion", "funding_divergence"),
        "limiting_factors": ("low_completeness",),
        "expected_events": ("volume_remains_expanded",),
        "observed_events": ("structure_break_observed",),
        "missing_expected_events": (),
        "unexpected_events": ("liquidity_sweep",),
        "transition_reason": "Initial normalized evidence recorded",
        "source_assessment_id": "assessment-1",
        "source_candidate_id": "candidate-1",
        "source_situation_id": None,
        "metadata": {"sequence": [1]},
    }
    values.update(overrides)
    return MarketSituationTimelineEntry(**values)


def make_timeline(entries=None, **overrides):
    if entries is None:
        entries = (make_entry(),)
    values = {
        "timeline_id": "timeline-1",
        "asset": "link",
        "created_at": BASE_TIME,
        "updated_at": entries[-1].created_at if entries else BASE_TIME,
        "entries": entries,
        "current_stage": entries[-1].stage if entries else EmergingStage.UNKNOWN,
        "version": 1,
        "metadata": {"owner": {"kind": "market_situation"}},
    }
    values.update(overrides)
    return MarketSituationTimeline(**values)


class SituationDNATests(unittest.TestCase):
    def test_valid_situation_dna(self):
        dna = make_dna()
        self.assertEqual(dna.volume_expansion, 74.0)
        self.assertEqual(dna.completeness, 62.5)

    def test_none_is_unavailable_and_zero_is_measured_zero(self):
        dna = make_dna(whale_activity=None, liquidity_event=0)
        self.assertIsNone(dna.whale_activity)
        self.assertEqual(dna.liquidity_event, 0.0)

    def test_dna_is_immutable_and_deeply_freezes_metadata(self):
        source = {"nested": {"values": [1, 2]}}
        dna = make_dna(metadata=source)
        source["nested"]["values"].append(3)
        self.assertIsInstance(dna.metadata, MappingProxyType)
        self.assertEqual(dna.metadata["nested"]["values"], (1, 2))
        with self.assertRaises(FrozenInstanceError):
            dna.quality = 2.0
        with self.assertRaises(TypeError):
            dna.metadata["new"] = "value"

    def test_factor_availability_is_sorted_and_immutable(self):
        dna = make_dna(factor_availability={"z": "MISSING", "a": "AVAILABLE"})
        self.assertEqual(tuple(dna.factor_availability), ("a", "z"))
        with self.assertRaises(TypeError):
            dna.factor_availability["x"] = "ERROR"

    def test_non_serializable_metadata_is_rejected(self):
        with self.assertRaises(TypeError):
            make_dna(metadata={"invalid": object()})

    def test_dna_serialization_round_trip(self):
        dna = make_dna()
        restored = SituationDNA.from_dict(dna.to_dict())
        self.assertEqual(restored, dna)
        self.assertIsInstance(restored.metadata, MappingProxyType)

    def test_all_percentage_fields_validate_bounds(self):
        for name in (
            "whale_activity",
            "completeness",
            "quality",
            "freshness",
            "opportunity",
            "priority",
            "maturity",
            "emergence",
            "horizon",
            "detection_confidence",
        ):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    make_dna(**{name: 100.01})

    def test_boolean_numeric_is_rejected(self):
        with self.assertRaises(TypeError):
            make_dna(volume_expansion=True)
        with self.assertRaises(TypeError):
            make_dna(completeness=False)

    def test_dna_has_no_direction_trade_or_outcome_fields(self):
        names = {item.name for item in fields(SituationDNA)}
        self.assertFalse(names & {"direction", "trade", "buy", "sell", "outcome"})


class TimelineEntryTests(unittest.TestCase):
    def test_valid_entry_preserves_emerging_stage(self):
        entry = make_entry(stage=EmergingStage.EMERGING)
        self.assertIs(entry.stage, EmergingStage.EMERGING)
        self.assertIsInstance(entry.dna, SituationDNA)

    def test_timestamp_is_utc_aware_and_normalized(self):
        plus_two = timezone(timedelta(hours=2))
        entry = make_entry(created_at=datetime(2026, 7, 15, 14, 0, tzinfo=plus_two))
        self.assertEqual(entry.created_at, BASE_TIME)
        with self.assertRaises(ValueError):
            make_entry(created_at=datetime(2026, 7, 15, 12, 0))

    def test_entry_is_immutable_and_collections_are_tuples(self):
        supporting = ["volume_expansion"]
        entry = make_entry(supporting_factors=supporting)
        supporting.append("momentum_shift")
        self.assertEqual(entry.supporting_factors, ("volume_expansion",))
        with self.assertRaises(FrozenInstanceError):
            entry.stage = EmergingStage.MATURE

    def test_duplicate_collections_are_rejected(self):
        for field_name in (
            "supporting_factors",
            "limiting_factors",
            "expected_events",
            "observed_events",
            "missing_expected_events",
            "unexpected_events",
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaises(ValueError):
                    make_entry(**{field_name: ("same", "same")})

    def test_expectation_collections_remain_distinct(self):
        entry = make_entry(
            observed_events=(),
            missing_expected_events=("price_follow_through",),
            unexpected_events=("funding_normalized",),
        )
        self.assertEqual(entry.observed_events, ())
        self.assertEqual(entry.missing_expected_events, ("price_follow_through",))
        self.assertEqual(entry.unexpected_events, ("funding_normalized",))

    def test_empty_observed_does_not_infer_missing(self):
        entry = make_entry(observed_events=(), missing_expected_events=())
        self.assertEqual(entry.observed_events, ())
        self.assertEqual(entry.missing_expected_events, ())

    def test_transition_reason_and_ids_validate(self):
        with self.assertRaises(ValueError):
            make_entry(transition_reason=" ")
        with self.assertRaises(ValueError):
            make_entry(entry_id="")
        with self.assertRaises(ValueError):
            make_entry(source_candidate_id=" ")

    def test_entry_serialization_round_trip(self):
        entry = make_entry(stage=EmergingStage.BUILDING)
        restored = MarketSituationTimelineEntry.from_dict(entry.to_dict())
        self.assertEqual(restored, entry)
        self.assertIs(restored.stage, EmergingStage.BUILDING)

    def test_entry_has_no_trade_direction_or_outcome_fields(self):
        names = {item.name for item in fields(MarketSituationTimelineEntry)}
        self.assertFalse(names & {"direction", "trade", "buy", "sell", "outcome"})


class MarketSituationTimelineTests(unittest.TestCase):
    def test_valid_timeline_and_asset_normalization(self):
        timeline = make_timeline()
        self.assertEqual(timeline.asset, "LINK")
        self.assertIs(timeline.current_stage, EmergingStage.SEED)

    def test_timeline_is_immutable_and_metadata_is_frozen(self):
        timeline = make_timeline()
        self.assertIsInstance(timeline.metadata, MappingProxyType)
        with self.assertRaises(FrozenInstanceError):
            timeline.version = 3

    def test_version_must_be_positive_integer(self):
        for value, exception in ((0, ValueError), (-1, ValueError), (True, TypeError), (1.2, TypeError)):
            with self.subTest(value=value):
                with self.assertRaises(exception):
                    make_timeline(version=value)

    def test_updated_at_must_not_precede_creation_or_last_entry(self):
        with self.assertRaises(ValueError):
            make_timeline(created_at=BASE_TIME, updated_at=BASE_TIME - timedelta(seconds=1))
        entry = make_entry(created_at=BASE_TIME + timedelta(minutes=2))
        with self.assertRaises(ValueError):
            make_timeline(entries=(entry,), updated_at=BASE_TIME)

    def test_entry_timeline_ids_must_match(self):
        with self.assertRaises(ValueError):
            make_timeline(entries=(make_entry(timeline_id="other"),))

    def test_duplicate_entry_ids_are_rejected(self):
        first = make_entry()
        second = make_entry(created_at=BASE_TIME + timedelta(minutes=1))
        with self.assertRaises(ValueError):
            make_timeline(entries=(first, second))

    def test_entries_must_be_in_non_decreasing_time_order(self):
        later = make_entry("later", created_at=BASE_TIME + timedelta(minutes=1))
        earlier = make_entry("earlier", created_at=BASE_TIME)
        with self.assertRaises(ValueError):
            make_timeline(entries=(later, earlier))

    def test_current_stage_must_match_last_entry(self):
        with self.assertRaises(ValueError):
            make_timeline(current_stage=EmergingStage.MATURE)

    def test_empty_timeline_requires_unknown(self):
        empty = make_timeline(entries=(), current_stage=EmergingStage.UNKNOWN)
        self.assertEqual(empty.entries, ())
        with self.assertRaises(ValueError):
            make_timeline(entries=(), current_stage=EmergingStage.SEED)

    def test_full_serialization_round_trip(self):
        second = make_entry(
            "entry-2",
            stage=EmergingStage.EMERGING,
            created_at=BASE_TIME + timedelta(minutes=5),
        )
        timeline = make_timeline(
            entries=(make_entry(), second),
            current_stage=EmergingStage.EMERGING,
            updated_at=second.created_at,
            version=2,
        )
        restored = MarketSituationTimeline.from_dict(timeline.to_dict())
        self.assertEqual(restored, timeline)
        self.assertIs(restored.entries[-1].stage, EmergingStage.EMERGING)

    def test_no_automatic_stage_progression(self):
        exhausted = make_entry(stage=EmergingStage.EXHAUSTED)
        timeline = make_timeline(entries=(exhausted,))
        seed = make_entry(
            "entry-2",
            stage=EmergingStage.SEED,
            created_at=BASE_TIME + timedelta(minutes=1),
        )
        replacement = append_timeline_entry(
            timeline, seed, updated_at=seed.created_at
        )
        self.assertIs(replacement.current_stage, EmergingStage.SEED)


class AppendTimelineEntryTests(unittest.TestCase):
    def test_append_returns_new_version_and_preserves_original(self):
        timeline = make_timeline()
        second = make_entry(
            "entry-2",
            stage=EmergingStage.EMERGING,
            created_at=BASE_TIME + timedelta(minutes=1),
        )
        replacement = append_timeline_entry(
            timeline, second, updated_at=second.created_at
        )
        self.assertIsNot(replacement, timeline)
        self.assertEqual(replacement.version, timeline.version + 1)
        self.assertEqual(replacement.entries, timeline.entries + (second,))
        self.assertIs(replacement.current_stage, EmergingStage.EMERGING)
        self.assertEqual(timeline.entries, (make_entry(),))
        self.assertEqual(timeline.version, 1)

    def test_append_to_empty_timeline(self):
        timeline = make_timeline(entries=())
        entry = make_entry(stage=EmergingStage.SEED)
        replacement = append_timeline_entry(timeline, entry, updated_at=BASE_TIME)
        self.assertEqual(replacement.entries, (entry,))

    def test_append_rejects_duplicate_and_mismatched_ids(self):
        timeline = make_timeline()
        with self.assertRaises(ValueError):
            append_timeline_entry(timeline, make_entry(), updated_at=BASE_TIME)
        other = make_entry(
            "other", timeline_id="different", created_at=BASE_TIME + timedelta(1)
        )
        with self.assertRaises(ValueError):
            append_timeline_entry(timeline, other, updated_at=other.created_at)

    def test_append_rejects_entry_time_regression(self):
        last = make_entry(created_at=BASE_TIME + timedelta(minutes=2))
        timeline = make_timeline(entries=(last,))
        earlier = make_entry("entry-2", created_at=BASE_TIME + timedelta(minutes=1))
        with self.assertRaises(ValueError):
            append_timeline_entry(timeline, earlier, updated_at=BASE_TIME + timedelta(minutes=3))

    def test_append_rejects_naive_or_early_updated_at(self):
        timeline = make_timeline()
        entry = make_entry("entry-2", created_at=BASE_TIME + timedelta(minutes=1))
        with self.assertRaises(ValueError):
            append_timeline_entry(timeline, entry, updated_at=datetime(2026, 7, 15, 12, 2))
        with self.assertRaises(ValueError):
            append_timeline_entry(timeline, entry, updated_at=BASE_TIME)


class DependencyBoundaryTests(unittest.TestCase):
    def test_runtime_imports_only_allowed_modules(self):
        package = Path("app/intelligence/timeline")
        allowed = (
            "app.intelligence.early_bird",
            "app.intelligence.timeline",
            "collections",
            "dataclasses",
            "datetime",
            "enum",
            "math",
            "numbers",
            "types",
            "typing",
        )
        forbidden = (
            "telegram",
            "fastapi",
            "database",
            "repository",
            "pipeline",
            "market_state",
            "experts",
            "scanner",
            "requests",
            "httpx",
            "socket",
        )
        for path in package.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            with self.subTest(path=path):
                self.assertTrue(all(name.startswith(allowed) for name in imports), imports)
                self.assertFalse(any(part in name.lower() for name in imports for part in forbidden), imports)


if __name__ == "__main__":
    unittest.main()
