"""Focused tests for immutable CandidateProjection contracts."""

import dataclasses
from datetime import datetime, timedelta, timezone
import inspect
import json
import unittest

from app.intelligence.projections import (
    CandidateProjection,
    EvidenceReferenceSnapshot,
    ProjectionFailureCategory,
    ProjectionValidationError,
)
from app.intelligence.reality_gap.enums import (
    RootCauseCategory,
    RootCauseDisposition,
    RootCauseRole,
)


NOW = datetime(2026, 7, 16, 6, tzinfo=timezone.utc)


def snapshot(**changes):
    values = dict(
        supporting_evidence_refs=("evidence-b", "evidence-a"),
        contradicting_evidence_refs=("evidence-c",),
        limitation_references=("limitation-b", "limitation-a"),
    )
    values.update(changes)
    return EvidenceReferenceSnapshot(**values)


def projection(**changes):
    values = dict(
        projection_id="projection:analysis-1:candidate-1",
        projection_version=1,
        candidate_id="candidate:candidate-1",
        candidate_version=3,
        projection_policy_version="projection-policy-v1",
        analysis_context_id="analysis:analysis-1",
        category=RootCauseCategory.FACTOR_NON_CONFIRMATION,
        role=RootCauseRole.CONTEXT_CANDIDATE,
        disposition=RootCauseDisposition.UNRESOLVED,
        tree_context_reference="tree-context:analysis-1",
        evidence_reference_snapshot=snapshot(),
        created_at=NOW,
        metadata={"lineage": {"source": "candidate-contract", "versions": [3, 1]}},
    )
    values.update(changes)
    return CandidateProjection(**values)


class CandidateProjectionContractTests(unittest.TestCase):
    def assert_category(self, expected, callable_value):
        with self.assertRaises(ProjectionValidationError) as caught:
            callable_value()
        self.assertEqual(caught.exception.category, expected)

    def test_immutable_construction_and_utc_normalization(self):
        value = projection(created_at=NOW.astimezone(timezone(timedelta(hours=3))))
        self.assertEqual(value.created_at, NOW)
        self.assertIs(value.created_at.tzinfo, timezone.utc)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.projection_version = 2

    def test_failure_categories_are_stable_public_values(self):
        expected = {
            "MISSING_IDENTITY",
            "VERSION_CONFLICT",
            "INVALID_EVIDENCE_REFERENCE",
            "INVALID_POLICY_VERSION",
            "INVALID_TREE_CONTEXT",
            "INVALID_TIMESTAMP",
            "MUTABLE_PAYLOAD",
        }
        self.assertEqual({item.value for item in ProjectionFailureCategory}, expected)
        for item in ProjectionFailureCategory:
            self.assertEqual(ProjectionFailureCategory(item.value), item)

    def test_mutation_rejection_and_defensive_freezing(self):
        metadata = {"nested": {"values": [1, 2]}}
        value = projection(metadata=metadata)
        metadata["nested"]["values"].append(3)
        self.assertEqual(value.metadata["nested"]["values"], (1, 2))
        with self.assertRaises(TypeError):
            value.metadata["new"] = "value"
        with self.assertRaises(TypeError):
            value.metadata["nested"]["values"][0] = 9

    def test_deterministic_serialization_and_stable_field_order(self):
        first = projection(metadata={"z": 1, "a": {"y": 2, "b": 3}})
        second = projection(metadata={"a": {"b": 3, "y": 2}, "z": 1})
        self.assertEqual(first, second)
        self.assertEqual(first.to_json_bytes(), second.to_json_bytes())
        self.assertEqual(
            tuple(first.to_dict()),
            (
                "projection_id", "projection_version", "candidate_id",
                "candidate_version", "projection_policy_version",
                "analysis_context_id", "category", "role", "disposition",
                "tree_context_reference", "evidence_reference_snapshot",
                "created_at", "metadata",
            ),
        )
        self.assertEqual(
            json.loads(first.to_json_bytes().decode("utf-8")),
            first.to_dict(),
        )

    def test_serialization_round_trip(self):
        value = projection()
        restored = CandidateProjection.from_dict(value.to_dict())
        self.assertEqual(restored, value)
        self.assertEqual(restored.to_json_bytes(), value.to_json_bytes())

    def test_candidate_projection_and_tree_identity_are_separate(self):
        value = projection()
        self.assertNotEqual(value.projection_id, value.candidate_id)
        self.assertNotEqual(value.projection_id, value.tree_context_reference)
        self.assertNotEqual(value.candidate_id, value.tree_context_reference)
        self.assertNotEqual(value.analysis_context_id, value.tree_context_reference)
        self.assert_category(
            ProjectionFailureCategory.MISSING_IDENTITY,
            lambda: projection(projection_id="candidate:candidate-1"),
        )

    def test_candidate_and_projection_versions_are_independent(self):
        first = projection(candidate_version=7, projection_version=2)
        revised = dataclasses.replace(first, projection_version=3)
        candidate_revised = dataclasses.replace(first, candidate_version=8)
        self.assertEqual(revised.candidate_version, 7)
        self.assertEqual(candidate_revised.projection_version, 2)
        self.assertEqual(first.projection_version, 2)

    def test_evidence_snapshot_preserved_and_canonical(self):
        value = projection()
        evidence = value.evidence_reference_snapshot
        self.assertEqual(evidence.supporting_evidence_refs, ("evidence-a", "evidence-b"))
        self.assertEqual(evidence.contradicting_evidence_refs, ("evidence-c",))
        self.assertEqual(evidence.limitation_references, ("limitation-a", "limitation-b"))
        self.assertEqual(
            EvidenceReferenceSnapshot.from_dict(evidence.to_dict()),
            evidence,
        )

    def test_invalid_identity_rejected(self):
        for field_name in ("projection_id", "candidate_id", "analysis_context_id"):
            self.assert_category(
                ProjectionFailureCategory.MISSING_IDENTITY,
                lambda field_name=field_name: projection(**{field_name: " "}),
            )
        self.assert_category(
            ProjectionFailureCategory.VERSION_CONFLICT,
            lambda: projection(projection_version=0),
        )
        self.assert_category(
            ProjectionFailureCategory.VERSION_CONFLICT,
            lambda: projection(candidate_version=True),
        )

    def test_invalid_timestamp_rejected(self):
        self.assert_category(
            ProjectionFailureCategory.INVALID_TIMESTAMP,
            lambda: projection(created_at=datetime(2026, 7, 16, 6)),
        )
        data = projection().to_dict()
        data["created_at"] = "not-a-time"
        self.assert_category(
            ProjectionFailureCategory.INVALID_TIMESTAMP,
            lambda: CandidateProjection.from_dict(data),
        )

    def test_invalid_evidence_rejected(self):
        self.assert_category(
            ProjectionFailureCategory.INVALID_EVIDENCE_REFERENCE,
            lambda: snapshot(supporting_evidence_refs=("evidence-a", "evidence-a")),
        )
        self.assert_category(
            ProjectionFailureCategory.INVALID_EVIDENCE_REFERENCE,
            lambda: snapshot(contradicting_evidence_refs=("evidence-a",)),
        )
        self.assert_category(
            ProjectionFailureCategory.INVALID_EVIDENCE_REFERENCE,
            lambda: snapshot(supporting_evidence_refs={"evidence-a"}),
        )
        self.assert_category(
            ProjectionFailureCategory.INVALID_EVIDENCE_REFERENCE,
            lambda: projection(evidence_reference_snapshot=("evidence-a",)),
        )

    def test_invalid_tree_context_rejected(self):
        for tree_context in (
            " ",
            "projection:analysis-1:candidate-1",
            "candidate:candidate-1",
            "analysis:analysis-1",
        ):
            self.assert_category(
                ProjectionFailureCategory.INVALID_TREE_CONTEXT,
                lambda tree_context=tree_context: projection(
                    tree_context_reference=tree_context
                ),
            )

    def test_mutable_or_unsupported_payload_rejected(self):
        self.assert_category(
            ProjectionFailureCategory.MUTABLE_PAYLOAD,
            lambda: projection(metadata={"unordered": {"a", "b"}}),
        )
        self.assert_category(
            ProjectionFailureCategory.MUTABLE_PAYLOAD,
            lambda: projection(metadata={"binary": bytearray(b"value")}),
        )
        self.assert_category(
            ProjectionFailureCategory.MUTABLE_PAYLOAD,
            lambda: projection(metadata={1: "not-a-string-key"}),
        )

    def test_policy_and_lineage_metadata_must_agree(self):
        self.assert_category(
            ProjectionFailureCategory.INVALID_POLICY_VERSION,
            lambda: projection(
                metadata={"projection_policy_version": "projection-policy-v2"}
            ),
        )
        self.assert_category(
            ProjectionFailureCategory.VERSION_CONFLICT,
            lambda: projection(metadata={"candidate_version": 99}),
        )

    def test_disposition_is_explicit_and_no_status_mapping_exists(self):
        value = projection(disposition=RootCauseDisposition.PARTIALLY_SUPPORTED)
        self.assertEqual(value.disposition, RootCauseDisposition.PARTIALLY_SUPPORTED)
        field_names = {item.name for item in dataclasses.fields(CandidateProjection)}
        self.assertNotIn("status", field_names)
        self.assertNotIn("confidence", field_names)
        self.assertNotIn("rank", field_names)

    def test_contract_has_no_tree_or_projection_engine(self):
        methods = {
            name
            for name, member in inspect.getmembers(CandidateProjection, inspect.isfunction)
            if not name.startswith("_")
        }
        self.assertEqual(methods, {"to_dict", "to_json_bytes"})


if __name__ == "__main__":
    unittest.main()
