"""Focused tests for the WR-035 Market Situation runtime contracts."""

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from app.intelligence.situations import (
    ConfidencePoint,
    ExpectationRecord,
    ExpectationStatus,
    ExpectationViolationType,
    MarketSituation,
    SituationHealth,
    SituationStage,
    SituationTimelineEntry,
    TimelineEventType,
)


UTC = timezone.utc
BASE_TIME = datetime(2026, 7, 14, 10, 0, tzinfo=UTC)


def make_timeline(
    entry_id="timeline-1",
    occurred_at=BASE_TIME,
    artifact_ids=("fast-1",),
):
    return SituationTimelineEntry(
        entry_id=entry_id,
        event_type=TimelineEventType.DETECTION,
        occurred_at=occurred_at,
        summary="Early event detected",
        artifact_ids=artifact_ids,
        metadata={"source": {"name": "fast"}},
    )


def make_confidence(recorded_at=BASE_TIME, value=45.0):
    return ConfidencePoint(
        recorded_at=recorded_at,
        value=value,
        source="shadow_intelligence",
        reason="Initial evidence attached",
        metadata={"inputs": ["legacy_intelligence"]},
    )


def make_expectation(
    expectation_id="expectation-1",
    created_at=BASE_TIME,
    status=ExpectationStatus.PENDING,
    violation_type=ExpectationViolationType.NONE,
    gap_severity=0.0,
    observed_event_ids=(),
):
    return ExpectationRecord(
        expectation_id=expectation_id,
        created_at=created_at,
        window_start=BASE_TIME,
        window_end=BASE_TIME + timedelta(hours=1),
        description="Volume should confirm the structure break",
        basis_artifact_ids=("fast-1",),
        status=status,
        expected_event_type="VOLUME_EXPANSION",
        observed_event_ids=observed_event_ids,
        violation_type=violation_type,
        gap_severity=gap_severity,
        learning_conclusion=None,
        metadata={"timeframe": "5m"},
    )


def make_situation(**overrides):
    values = {
        "situation_id": "situation-1",
        "asset": " btcusdt ",
        "created_at": BASE_TIME,
        "updated_at": BASE_TIME + timedelta(minutes=5),
        "stage": SituationStage.DETECTED,
        "health": SituationHealth.UNKNOWN,
        "version": 1,
        "fast_event_ids": ("fast-1",),
        "observation_ids": ("observation-1",),
        "expert_opinion_ids": ("opinion-1",),
        "expert_names": ("trend_expert",),
        "correlation_ids": (),
        "market_state_ids": (),
        "decision_context_ids": (),
        "outcome_ids": (),
        "learning_record_ids": (),
        "memory_reference_ids": (),
        "timeline": (make_timeline(),),
        "confidence_history": (make_confidence(),),
        "expectation_history": (make_expectation(),),
        "metadata": {"nested": {"sources": ["fast", "trend"]}},
    }
    values.update(overrides)
    return MarketSituation(**values)


class MarketSituationTests(unittest.TestCase):
    def test_valid_market_situation_creation(self):
        situation = make_situation()
        self.assertEqual("situation-1", situation.situation_id)
        self.assertEqual(SituationStage.DETECTED, situation.stage)

    def test_models_are_immutable(self):
        situation = make_situation()
        with self.assertRaises(FrozenInstanceError):
            situation.version = 2

    def test_asset_is_normalized_uppercase(self):
        self.assertEqual("BTCUSDT", make_situation().asset)

    def test_invalid_version_is_rejected(self):
        for value in (0, -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                make_situation(version=value)
        for value in (True, 1.5, "1"):
            with self.subTest(value=value), self.assertRaises(TypeError):
                make_situation(version=value)

    def test_naive_timestamps_are_rejected(self):
        with self.assertRaises(ValueError):
            make_situation(created_at=datetime(2026, 7, 14, 10, 0))

    def test_timestamps_are_normalized_to_utc(self):
        offset = timezone(timedelta(hours=3))
        local_time = datetime(2026, 7, 14, 13, 0, tzinfo=offset)
        situation = make_situation(created_at=local_time, updated_at=local_time)
        self.assertEqual(BASE_TIME, situation.created_at)
        self.assertIs(UTC, situation.created_at.tzinfo)

    def test_updated_at_before_created_at_is_rejected(self):
        with self.assertRaises(ValueError):
            make_situation(updated_at=BASE_TIME - timedelta(seconds=1))

    def test_duplicate_artifact_references_are_rejected(self):
        with self.assertRaises(ValueError):
            make_situation(fast_event_ids=("fast-1", "fast-1"))

    def test_timeline_must_be_ordered(self):
        later = make_timeline("later", BASE_TIME + timedelta(minutes=1))
        earlier = make_timeline("earlier", BASE_TIME)
        with self.assertRaises(ValueError):
            make_situation(timeline=(later, earlier))

    def test_confidence_history_must_be_ordered(self):
        later = make_confidence(BASE_TIME + timedelta(minutes=1))
        earlier = make_confidence(BASE_TIME)
        with self.assertRaises(ValueError):
            make_situation(confidence_history=(later, earlier))

    def test_expectation_history_has_deterministic_creation_order(self):
        second = make_expectation("expectation-b")
        first = make_expectation("expectation-a")
        with self.assertRaises(ValueError):
            make_situation(expectation_history=(second, first))
        situation = make_situation(expectation_history=(first, second))
        self.assertEqual(
            ("expectation-a", "expectation-b"),
            tuple(item.expectation_id for item in situation.expectation_history),
        )

    def test_serialization_round_trip(self):
        original = make_situation()
        restored = MarketSituation.from_dict(original.to_dict())
        self.assertEqual(original, restored)
        self.assertEqual(SituationStage.DETECTED, restored.stage)
        self.assertEqual(ExpectationStatus.PENDING, restored.expectation_history[0].status)

    def test_metadata_is_deeply_frozen_and_defensively_copied(self):
        metadata = {"nested": {"values": [1, 2]}}
        situation = make_situation(metadata=metadata)
        metadata["nested"]["values"].append(3)
        self.assertEqual((1, 2), situation.metadata["nested"]["values"])
        with self.assertRaises(TypeError):
            situation.metadata["new"] = "value"
        with self.assertRaises(TypeError):
            situation.metadata["nested"]["new"] = "value"

    def test_raw_artifact_objects_cannot_be_stored_as_references(self):
        with self.assertRaises(TypeError):
            make_situation(fast_event_ids=(object(),))

    def test_no_automatic_stage_or_health_calculation(self):
        situation = make_situation(
            stage=SituationStage.MEMORY,
            health=SituationHealth.HEALTHY,
            timeline=(),
            confidence_history=(),
            expectation_history=(),
        )
        self.assertEqual(SituationStage.MEMORY, situation.stage)
        self.assertEqual(SituationHealth.HEALTHY, situation.health)

    def test_contract_has_no_trade_or_execution_fields(self):
        field_names = {item.name for item in fields(MarketSituation)}
        forbidden = {"signal", "recommendation", "buy", "sell", "tp", "sl", "execution"}
        self.assertTrue(field_names.isdisjoint(forbidden))


class PublicEnumTests(unittest.TestCase):
    def test_public_enum_values_match_wr_035_contract(self):
        self.assertEqual(
            (
                "DETECTED",
                "OBSERVED",
                "ANALYZED",
                "CORRELATED",
                "DECISION_SUPPORT",
                "OUTCOME",
                "LEARNING",
                "MEMORY",
            ),
            tuple(item.value for item in SituationStage),
        )
        self.assertEqual(
            ("HEALTHY", "WEAKENING", "CONTRADICTED", "INVALIDATED", "UNKNOWN"),
            tuple(item.value for item in SituationHealth),
        )
        self.assertEqual(16, len(TimelineEventType))
        self.assertEqual(
            ("PENDING", "FULFILLED", "MISSING", "CONTRADICTED", "EXPIRED", "CANCELLED"),
            tuple(item.value for item in ExpectationStatus),
        )
        self.assertEqual(
            ("NONE", "UNEXPECTED_EVENT", "MISSING_EXPECTED_EVENT", "BOTH", "UNKNOWN"),
            tuple(item.value for item in ExpectationViolationType),
        )


class TimelineEntryTests(unittest.TestCase):
    def test_entry_requires_id_and_summary(self):
        with self.assertRaises(ValueError):
            make_timeline(entry_id=" ")
        with self.assertRaises(ValueError):
            SituationTimelineEntry(
                entry_id="entry-1",
                event_type=TimelineEventType.DETECTION,
                occurred_at=BASE_TIME,
                summary="",
                artifact_ids=(),
                metadata={},
            )

    def test_duplicate_timeline_artifact_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            make_timeline(artifact_ids=("fast-1", "fast-1"))

    def test_timeline_round_trip_preserves_enum_and_timestamp(self):
        entry = make_timeline()
        restored = SituationTimelineEntry.from_dict(entry.to_dict())
        self.assertEqual(entry, restored)
        self.assertEqual(TimelineEventType.DETECTION, restored.event_type)
        self.assertIs(UTC, restored.occurred_at.tzinfo)


class ConfidencePointTests(unittest.TestCase):
    def test_confidence_boundaries_are_accepted(self):
        self.assertEqual(0.0, make_confidence(value=0).value)
        self.assertEqual(100.0, make_confidence(value=100).value)

    def test_invalid_confidence_values_are_rejected(self):
        for value in (-0.1, 100.1, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                make_confidence(value=value)
        with self.assertRaises(TypeError):
            make_confidence(value=True)

    def test_confidence_source_and_reason_are_required(self):
        with self.assertRaises(ValueError):
            ConfidencePoint(BASE_TIME, 50, "", "reason", {})
        with self.assertRaises(ValueError):
            ConfidencePoint(BASE_TIME, 50, "source", "", {})


class ExpectationRecordTests(unittest.TestCase):
    def test_valid_pending_expectation_can_have_zero_severity(self):
        expectation = make_expectation()
        self.assertEqual(ExpectationStatus.PENDING, expectation.status)
        self.assertEqual(0.0, expectation.gap_severity)
        self.assertEqual(ExpectationViolationType.NONE, expectation.violation_type)

    def test_invalid_expectation_window_is_rejected(self):
        with self.assertRaises(ValueError):
            ExpectationRecord(
                expectation_id="expectation-1",
                created_at=BASE_TIME,
                window_start=BASE_TIME + timedelta(hours=2),
                window_end=BASE_TIME + timedelta(hours=1),
                description="Expected event",
                basis_artifact_ids=("artifact-1",),
                status=ExpectationStatus.PENDING,
                expected_event_type="EVENT",
                observed_event_ids=(),
                violation_type=ExpectationViolationType.NONE,
                gap_severity=0,
                learning_conclusion=None,
                metadata={},
            )

    def test_created_at_after_window_end_is_rejected(self):
        with self.assertRaises(ValueError):
            ExpectationRecord(
                expectation_id="expectation-1",
                created_at=BASE_TIME + timedelta(hours=2),
                window_start=BASE_TIME,
                window_end=BASE_TIME + timedelta(hours=1),
                description="Expected event",
                basis_artifact_ids=("artifact-1",),
                status=ExpectationStatus.PENDING,
                expected_event_type="EVENT",
                observed_event_ids=(),
                violation_type=ExpectationViolationType.NONE,
                gap_severity=0,
                learning_conclusion=None,
                metadata={},
            )

    def test_gap_severity_boundaries_and_boolean_rejection(self):
        self.assertEqual(0.0, make_expectation(gap_severity=0).gap_severity)
        self.assertEqual(100.0, make_expectation(gap_severity=100).gap_severity)
        for value in (-1, 101):
            with self.subTest(value=value), self.assertRaises(ValueError):
                make_expectation(gap_severity=value)
        with self.assertRaises(TypeError):
            make_expectation(gap_severity=False)

    def test_basis_references_are_required_and_preserved(self):
        expectation = make_expectation()
        self.assertEqual(("fast-1",), expectation.basis_artifact_ids)
        values = expectation.to_dict()
        values["basis_artifact_ids"] = []
        with self.assertRaises(ValueError):
            ExpectationRecord.from_dict(values)

    def test_unexpected_event_violation_is_represented(self):
        expectation = make_expectation(
            status=ExpectationStatus.CONTRADICTED,
            violation_type=ExpectationViolationType.UNEXPECTED_EVENT,
            observed_event_ids=("event-unexpected",),
            gap_severity=80,
        )
        self.assertEqual(ExpectationViolationType.UNEXPECTED_EVENT, expectation.violation_type)

    def test_missing_expected_event_violation_is_represented(self):
        expectation = make_expectation(
            status=ExpectationStatus.MISSING,
            violation_type=ExpectationViolationType.MISSING_EXPECTED_EVENT,
            gap_severity=75,
        )
        self.assertEqual(ExpectationViolationType.MISSING_EXPECTED_EVENT, expectation.violation_type)

    def test_both_violation_types_are_represented(self):
        expectation = make_expectation(
            status=ExpectationStatus.CONTRADICTED,
            violation_type=ExpectationViolationType.BOTH,
            observed_event_ids=("event-unexpected",),
            gap_severity=100,
        )
        self.assertEqual(ExpectationViolationType.BOTH, expectation.violation_type)

    def test_missing_data_is_not_automatically_marked_missing(self):
        expectation = make_expectation(observed_event_ids=())
        self.assertEqual(ExpectationStatus.PENDING, expectation.status)
        self.assertEqual(ExpectationViolationType.NONE, expectation.violation_type)

    def test_expectation_round_trip_preserves_evaluation(self):
        original = make_expectation(
            status=ExpectationStatus.CONTRADICTED,
            violation_type=ExpectationViolationType.UNEXPECTED_EVENT,
            observed_event_ids=("event-2",),
            gap_severity=60,
        )
        restored = ExpectationRecord.from_dict(original.to_dict())
        self.assertEqual(original, restored)


class DependencyBoundaryTests(unittest.TestCase):
    def test_situations_import_only_standard_library_and_own_package(self):
        package = Path(__file__).parent / "app" / "intelligence" / "situations"
        for path in package.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("app."):
                        self.assertTrue(
                            node.module.startswith("app.intelligence.situations"),
                            "forbidden local import in {0}: {1}".format(path, node.module),
                        )
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertFalse(
                            alias.name.startswith("app."),
                            "forbidden local import in {0}: {1}".format(path, alias.name),
                        )


if __name__ == "__main__":
    unittest.main()
