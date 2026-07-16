"""Focused tests for immutable mapping contracts and the pure mapper."""

import dataclasses
from datetime import datetime, timedelta, timezone
import unittest

from app.intelligence.projections import (
    CandidateProjection,
    EvidenceCatalogEntry,
    EvidenceCatalogView,
    EvidenceReferenceSnapshot,
    ExplanationDecisionSnapshot,
    ExplanationDescriptorSnapshot,
    MappingFailureCategory,
    RootCauseCandidateMappingFailure,
    RootCauseCandidateMappingRequest,
    RootCauseCandidateMappingResult,
    TreePlacementSnapshot,
    map_projection_to_root_cause_candidate,
)
from app.intelligence.reality_gap import (
    RealityGapEvidenceEligibility,
    RootCauseCategory,
    RootCauseDisposition,
    RootCauseRole,
)


EVIDENCE_TIME = datetime(2026, 7, 16, 5, tzinfo=timezone.utc)
PROJECTION_TIME = datetime(2026, 7, 16, 6, tzinfo=timezone.utc)
MAPPING_TIME = datetime(2026, 7, 16, 7, tzinfo=timezone.utc)


def source_projection():
    return CandidateProjection(
        projection_id="projection:analysis-1:candidate-1",
        projection_version=2,
        candidate_id="candidate:candidate-1",
        candidate_version=4,
        projection_policy_version="projection-policy-v1",
        analysis_context_id="analysis:analysis-1",
        category=RootCauseCategory.FACTOR_NON_CONFIRMATION,
        role=RootCauseRole.CONTEXT_CANDIDATE,
        disposition=RootCauseDisposition.UNRESOLVED,
        tree_context_reference="tree-context:analysis-1",
        evidence_reference_snapshot=EvidenceReferenceSnapshot(
            supporting_evidence_refs=("evidence-support",),
            contradicting_evidence_refs=("evidence-contradiction",),
            limitation_references=("limitation:single-source",),
        ),
        created_at=PROJECTION_TIME,
        metadata={"source": "approved-projection"},
    )


def descriptor(**changes):
    values = dict(
        candidate_id="candidate:candidate-1",
        candidate_version=4,
        subject="volume",
        description="Volume confirmation remained incomplete in the eligible window.",
        hypothesis_reference="hypothesis:volume-non-confirmation",
        descriptor_policy_version="descriptor-policy-v1",
        created_at=PROJECTION_TIME,
        metadata={"kind": "explicit"},
    )
    values.update(changes)
    return ExplanationDescriptorSnapshot(**values)


def decision(**changes):
    values = dict(
        projection_id="projection:analysis-1:candidate-1",
        projection_version=2,
        role=RootCauseRole.CONTEXT_CANDIDATE,
        disposition=RootCauseDisposition.UNRESOLVED,
        decision_reference="decision:analysis-1:candidate-1",
        independent_support_count=1,
        independent_support_provenance_reference="support-provenance:analysis-1",
        rejection_reason=None,
        decision_policy_version="decision-policy-v1",
        mapping_policy_version="mapping-policy-v1",
        created_at=PROJECTION_TIME,
        metadata={"explicit": True},
    )
    values.update(changes)
    return ExplanationDecisionSnapshot(**values)


def placement(**changes):
    values = dict(
        tree_context_reference="tree-context:analysis-1",
        tree_version="tree-v1",
        target_projection_id="projection:analysis-1:candidate-1",
        parent_projection_id=None,
        child_projection_ids=(),
        alternative_projection_ids=("projection:analysis-1:alternative-1",),
        placement_policy_version="placement-policy-v1",
        created_at=PROJECTION_TIME,
        metadata={"declared": True},
    )
    values.update(changes)
    return TreePlacementSnapshot(**values)


def catalog(*entries):
    if not entries:
        entries = (
            EvidenceCatalogEntry(
                "evidence-support",
                RealityGapEvidenceEligibility.ELIGIBLE,
                EVIDENCE_TIME,
                {"relation": "support"},
            ),
            EvidenceCatalogEntry(
                "evidence-contradiction",
                RealityGapEvidenceEligibility.INELIGIBLE,
                EVIDENCE_TIME,
                {"relation": "contradiction"},
            ),
        )
    return EvidenceCatalogView(
        catalog_id="catalog:analysis-1",
        catalog_version="catalog-v1",
        entries=entries,
        created_at=PROJECTION_TIME,
        metadata={"historical": True},
    )


def request(**changes):
    values = dict(
        source_projection=source_projection(),
        explanation_descriptor=descriptor(),
        explanation_decision_snapshot=decision(),
        placement_snapshot=placement(),
        evidence_catalog_view=catalog(),
        mapping_policy_version="mapping-policy-v1",
        created_at=MAPPING_TIME,
        metadata={"request": {"sequence": [1, 2]}},
    )
    values.update(changes)
    return RootCauseCandidateMappingRequest(**values)


class ProjectionMappingTests(unittest.TestCase):
    def test_valid_mapping_and_field_transfer(self):
        outcome = map_projection_to_root_cause_candidate(request())
        self.assertIsInstance(outcome, RootCauseCandidateMappingResult)
        candidate = outcome.root_cause_candidate
        self.assertEqual(candidate.candidate_id, "projection:analysis-1:candidate-1")
        self.assertEqual(candidate.category, RootCauseCategory.FACTOR_NON_CONFIRMATION)
        self.assertEqual(candidate.subject, "volume")
        self.assertEqual(candidate.role, RootCauseRole.CONTEXT_CANDIDATE)
        self.assertEqual(candidate.disposition, RootCauseDisposition.UNRESOLVED)
        self.assertEqual(candidate.supporting_evidence_refs, ("evidence-support",))
        self.assertEqual(candidate.contradicting_evidence_refs, ("evidence-contradiction",))
        self.assertEqual(candidate.limitations, ("limitation:single-source",))
        self.assertEqual(candidate.alternative_candidate_ids, ("projection:analysis-1:alternative-1",))
        self.assertIsNone(candidate.confidence)
        self.assertIsNone(candidate.temporal_precedence)
        self.assertIsNone(candidate.direct_relevance)
        self.assertIsNone(candidate.evidence_coverage)

    def test_deterministic_result_and_serialization(self):
        first = map_projection_to_root_cause_candidate(request())
        second = map_projection_to_root_cause_candidate(request())
        self.assertEqual(first, second)
        self.assertEqual(first.to_json_bytes(), second.to_json_bytes())
        restored = RootCauseCandidateMappingResult.from_dict(first.to_dict())
        self.assertEqual(restored, first)
        self.assertEqual(restored.to_json_bytes(), first.to_json_bytes())

    def test_request_is_immutable_and_round_trips(self):
        value = request()
        restored = RootCauseCandidateMappingRequest.from_dict(value.to_dict())
        self.assertEqual(restored, value)
        self.assertEqual(restored.to_json_bytes(), value.to_json_bytes())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.mapping_policy_version = "mapping-policy-v2"
        with self.assertRaises(TypeError):
            value.metadata["new"] = True

    def test_result_is_immutable(self):
        outcome = map_projection_to_root_cause_candidate(request())
        with self.assertRaises(dataclasses.FrozenInstanceError):
            outcome.source_projection_version = 3
        with self.assertRaises(dataclasses.FrozenInstanceError):
            outcome.root_cause_candidate = None

    def test_lineage_preservation_and_identity_separation(self):
        outcome = map_projection_to_root_cause_candidate(request())
        self.assertEqual(outcome.source_candidate_id, "candidate:candidate-1")
        self.assertEqual(outcome.source_candidate_version, 4)
        self.assertEqual(outcome.source_projection_id, "projection:analysis-1:candidate-1")
        self.assertEqual(outcome.source_projection_version, 2)
        self.assertNotEqual(outcome.source_candidate_id, outcome.source_projection_id)
        metadata = outcome.root_cause_candidate.metadata
        self.assertEqual(metadata["source_candidate_id"], outcome.source_candidate_id)
        self.assertEqual(metadata["source_candidate_version"], 4)
        self.assertEqual(metadata["source_projection_version"], 2)
        self.assertEqual(metadata["hypothesis_reference"], "hypothesis:volume-non-confirmation")

    def test_missing_decision_returns_failure_without_partial_candidate(self):
        outcome = map_projection_to_root_cause_candidate(
            request(explanation_decision_snapshot=None)
        )
        self.assertIsInstance(outcome, RootCauseCandidateMappingFailure)
        self.assertEqual(outcome.category, MappingFailureCategory.MISSING_DECISION_SNAPSHOT)
        self.assertNotIn("root_cause_candidate", outcome.to_dict())
        self.assertFalse(outcome.metadata["partial_candidate_created"])
        self.assertEqual(
            RootCauseCandidateMappingFailure.from_dict(outcome.to_dict()),
            outcome,
        )
        self.assertEqual(
            RootCauseCandidateMappingFailure.from_dict(outcome.to_dict()).to_json_bytes(),
            outcome.to_json_bytes(),
        )

    def test_unknown_projection_and_lineage_mismatch_failures(self):
        unknown = map_projection_to_root_cause_candidate(request(source_projection=None))
        self.assertEqual(unknown.category, MappingFailureCategory.UNKNOWN_PROJECTION)
        mismatch = map_projection_to_root_cause_candidate(
            request(explanation_descriptor=descriptor(candidate_version=99))
        )
        self.assertEqual(mismatch.category, MappingFailureCategory.LINEAGE_MISMATCH)

    def test_invalid_evidence_returns_failure(self):
        missing_catalog_entry = catalog(
            EvidenceCatalogEntry(
                "evidence-support",
                RealityGapEvidenceEligibility.ELIGIBLE,
                EVIDENCE_TIME,
                {},
            )
        )
        missing = map_projection_to_root_cause_candidate(
            request(evidence_catalog_view=missing_catalog_entry)
        )
        self.assertEqual(missing.category, MappingFailureCategory.INVALID_EVIDENCE_REFERENCE)
        ineligible_support = catalog(
            EvidenceCatalogEntry(
                "evidence-support",
                RealityGapEvidenceEligibility.INELIGIBLE,
                EVIDENCE_TIME,
                {},
            ),
            EvidenceCatalogEntry(
                "evidence-contradiction",
                RealityGapEvidenceEligibility.INELIGIBLE,
                EVIDENCE_TIME,
                {},
            ),
        )
        ineligible = map_projection_to_root_cause_candidate(
            request(evidence_catalog_view=ineligible_support)
        )
        self.assertEqual(ineligible.category, MappingFailureCategory.INVALID_EVIDENCE_REFERENCE)

        extra = catalog(
            EvidenceCatalogEntry(
                "evidence-support",
                RealityGapEvidenceEligibility.ELIGIBLE,
                EVIDENCE_TIME,
                {},
            ),
            EvidenceCatalogEntry(
                "evidence-contradiction",
                RealityGapEvidenceEligibility.INELIGIBLE,
                EVIDENCE_TIME,
                {},
            ),
            EvidenceCatalogEntry(
                "evidence-unrelated",
                RealityGapEvidenceEligibility.ELIGIBLE,
                EVIDENCE_TIME,
                {},
            ),
        )
        unscoped = map_projection_to_root_cause_candidate(
            request(evidence_catalog_view=extra)
        )
        self.assertEqual(unscoped.category, MappingFailureCategory.INVALID_EVIDENCE_REFERENCE)

    def test_future_evidence_is_rejected(self):
        future_catalog = catalog(
            EvidenceCatalogEntry(
                "evidence-support",
                RealityGapEvidenceEligibility.ELIGIBLE,
                PROJECTION_TIME + timedelta(minutes=1),
                {},
            ),
            EvidenceCatalogEntry(
                "evidence-contradiction",
                RealityGapEvidenceEligibility.INELIGIBLE,
                EVIDENCE_TIME,
                {},
            ),
        )
        outcome = map_projection_to_root_cause_candidate(
            request(evidence_catalog_view=future_catalog)
        )
        self.assertEqual(outcome.category, MappingFailureCategory.INVALID_EVIDENCE_REFERENCE)

    def test_policy_conflict_returns_failure(self):
        outcome = map_projection_to_root_cause_candidate(
            request(
                explanation_decision_snapshot=decision(
                    mapping_policy_version="mapping-policy-v2"
                )
            )
        )
        self.assertEqual(outcome.category, MappingFailureCategory.POLICY_CONFLICT)

    def test_placement_validation_failure(self):
        outcome = map_projection_to_root_cause_candidate(
            request(
                placement_snapshot=placement(
                    tree_context_reference="tree-context:other-analysis"
                )
            )
        )
        self.assertEqual(outcome.category, MappingFailureCategory.INVALID_PLACEMENT_CONTEXT)

    def test_explicit_decision_mismatch_is_not_inferred(self):
        outcome = map_projection_to_root_cause_candidate(
            request(
                explanation_decision_snapshot=decision(
                    disposition=RootCauseDisposition.ACCEPTED
                )
            )
        )
        self.assertEqual(outcome.category, MappingFailureCategory.MISSING_DECISION_SNAPSHOT)

    def test_no_side_effects(self):
        value = request()
        before = value.to_json_bytes()
        first = map_projection_to_root_cause_candidate(value)
        second = map_projection_to_root_cause_candidate(value)
        self.assertEqual(value.to_json_bytes(), before)
        self.assertEqual(first, second)
        self.assertEqual(value.source_projection.to_dict(), source_projection().to_dict())

    def test_failure_categories_are_stable(self):
        expected = {
            "UNKNOWN_PROJECTION",
            "LINEAGE_MISMATCH",
            "INVALID_EVIDENCE_REFERENCE",
            "MISSING_DECISION_SNAPSHOT",
            "POLICY_CONFLICT",
            "INVALID_PLACEMENT_CONTEXT",
        }
        self.assertEqual({item.value for item in MappingFailureCategory}, expected)


if __name__ == "__main__":
    unittest.main()
