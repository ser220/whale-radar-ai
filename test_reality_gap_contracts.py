"""Focused tests for PS-4 Step 7C Reality Gap contracts."""

import dataclasses
from datetime import datetime, timedelta, timezone
import inspect
import unittest

from app.intelligence.reality_gap import (
    AnalysisCapabilities,
    AnalysisProvenance,
    ExplanationGapRecord,
    IntelligenceGapType,
    ObservabilityGapRecord,
    ObservabilityGapType,
    RealityGapAnalysis,
    RealityGapDecisionTrace,
    RealityGapDimension,
    RealityGapEvidenceEligibility,
    RealityGapEvidenceReference,
    RealityGapEvidenceRelation,
    RealityGapEvidenceType,
    RealityGapPrimaryType,
    RealityGapSeverity,
    RootCauseCandidate,
    RootCauseCategory,
    RootCauseDisposition,
    RootCauseRole,
    RootCauseTree,
    canonical_json_bytes,
    validate_analysis_revision,
    validate_root_cause_tree,
)


NOW = datetime(2026, 7, 15, 12, tzinfo=timezone.utc)


def provenance(metric="metric-v1"):
    return AnalysisProvenance(
        "engine-v1", "classification-v1", "candidate-v1", metric, "severity-v1",
        "tree-v1", "trace-v1", "taxonomy-v1", "json-v1", "reality_gap_engine",
        {"build": {"revision": 1}},
    )


def capabilities(**changes):
    values = dict(
        supports_market_gap=True, supports_intelligence_gap=True,
        supports_observability_gap=True, supports_explanation_gap=True,
        supports_root_cause_candidates=True, supports_root_cause_tree=True,
        supports_knowledge_gap_metric=True,
        supports_explanation_confidence_metric=True,
        supports_severity=True, supports_decision_trace=True,
        metadata={"phase": "7C"},
    )
    values.update(changes)
    return AnalysisCapabilities(**values)


def evidence(evidence_id="ev-1", eligibility=RealityGapEvidenceEligibility.ELIGIBLE,
             measured_value=0.0, availability="AVAILABLE", rejection_reason=None):
    return RealityGapEvidenceReference(
        evidence_id=evidence_id,
        evidence_type=RealityGapEvidenceType.EVALUATION_FACT,
        relation=RealityGapEvidenceRelation.SUPPORTS,
        eligibility=eligibility,
        artifact_id="evaluation-1", timeline_id="timeline-1", timeline_version=1,
        entry_id="entry-1", observed_at=NOW, factor_name="volume",
        measured_value=measured_value, availability=availability, delta_state="WEAKENED",
        prior_value=70.0, new_value=40.0, criterion_reference="criterion-1",
        rejection_reason=rejection_reason, quality=80.0, metadata={"rank": [1, 2]},
    )


def candidate(candidate_id="candidate-1", disposition=RootCauseDisposition.ACCEPTED,
              role=RootCauseRole.PRIMARY_CANDIDATE, parent=None, children=(),
              alternatives=(), refs=("ev-1",), rejection_reason=None):
    return RootCauseCandidate(
        candidate_id=candidate_id, category=RootCauseCategory.FACTOR_WEAKENING,
        subject="volume", description="Volume evidence weakened within the eligible window.",
        role=role, disposition=disposition, confidence=75.0, temporal_precedence=80.0,
        direct_relevance=70.0, evidence_coverage=60.0, independent_support_count=1,
        supporting_evidence_refs=refs, contradicting_evidence_refs=(),
        parent_candidate_id=parent, child_candidate_ids=children, limitations=("single source",),
        alternative_candidate_ids=alternatives, rejection_reason=rejection_reason,
        policy_version="candidate-v1", metadata={"order": 1},
    )


def tree(candidates=("candidate-1",), roots=("candidate-1",), accepted=("candidate-1",),
         rejected=(), unresolved=(), edges=(), maximum_depth=1):
    return RootCauseTree(
        "tree-1", "tree-v1", candidates, roots, accepted, rejected, unresolved,
        edges, maximum_depth, {"kind": "declared"},
    )


def trace(considered=("ev-1",), rejected=()):
    return RealityGapDecisionTrace(
        trace_id="trace-1", trace_version="trace-v1", expectation_status="MISSED",
        evaluation_gap_type="MISSING_EXPECTED_REALITY",
        eligible_window_start=NOW - timedelta(hours=1), eligible_window_end=NOW,
        evidence_considered=considered, evidence_rejected=rejected,
        gap_dimensions_considered=(RealityGapDimension.MARKET, RealityGapDimension.EXPLANATION),
        classification_steps=("Read immutable evaluation classification.",),
        candidate_generation_steps=("Receive externally generated candidates.",),
        candidate_acceptance_steps=("Record accepted disposition.",),
        candidate_rejection_steps=(), metric_inputs={"surprise": 55.0},
        metric_outputs={"surprise": 55.0}, severity_inputs={"declared": "MEDIUM"},
        severity_output=RealityGapSeverity.MEDIUM, unresolved_questions=("Was coverage sufficient?",),
        policy_versions={"classification": "classification-v1"}, created_at=NOW,
        metadata={"audit": True},
    )


def analysis(**changes):
    ev = evidence()
    cause = candidate()
    values = dict(
        gap_id="gap-1", expectation_id="expectation-1", evaluation_id="evaluation-1",
        timeline_id="timeline-1", asset="btc", analysis_version=1, created_at=NOW,
        evaluated_at=NOW, primary_type=RealityGapPrimaryType.MISSING_EXPECTED_REALITY,
        dimensions=(RealityGapDimension.MARKET, RealityGapDimension.EXPLANATION),
        intelligence_gap_types=(IntelligenceGapType.INTERPRETATION_GAP,),
        observability_gap_types=(), severity=RealityGapSeverity.MEDIUM,
        surprise_score=55.0, knowledge_gap_score=20.0, explanation_confidence=65.0,
        unexplained_residual_score=35.0, missing_expected_events=("volume follow-through",),
        unexpected_events=(), contradictory_events=(), fulfilled_events=("structure held",),
        root_cause_candidates=(cause,), root_cause_tree=tree(),
        accepted_candidate_ids=("candidate-1",), rejected_candidate_ids=(),
        unresolved_candidate_ids=(), supporting_evidence=(ev,), observability_gaps=(),
        explanation_gap=ExplanationGapRecord(35.0, 0, 1, 1, (), ("single source",),
                                              "Some residual remains.", "explanation-v1", {}),
        source_expectation_snapshot={"expectation_id": "expectation-1", "status": "ACTIVE"},
        source_evaluation_snapshot={"evaluation_id": "evaluation-1", "timeline_id": "timeline-1"},
        source_timeline_versions=(1,), source_entry_ids=("entry-1",),
        analysis_policy_version="classification-v1", metric_version="metric-v1",
        taxonomy_version="taxonomy-v1", tree_version="tree-v1", trace_version="trace-v1",
        provenance=provenance(), analysis_capabilities=capabilities(), decision_trace=trace(),
        revision_reason=None, metadata={"labels": ["baseline"]},
    )
    values.update(changes)
    return RealityGapAnalysis(**values)


class EnumTests(unittest.TestCase):
    def test_every_enum_round_trip(self):
        enum_types = (
            RealityGapDimension, RealityGapPrimaryType, IntelligenceGapType,
            ObservabilityGapType, RealityGapSeverity, RootCauseCategory,
            RootCauseRole, RootCauseDisposition, RealityGapEvidenceType,
            RealityGapEvidenceRelation, RealityGapEvidenceEligibility,
        )
        for enum_type in enum_types:
            for member in enum_type:
                self.assertEqual(enum_type(member.value), member)


class ComponentContractTests(unittest.TestCase):
    def test_provenance_round_trip_and_immutability(self):
        model = provenance()
        self.assertEqual(AnalysisProvenance.from_dict(model.to_dict()), model)
        with self.assertRaises((TypeError, dataclasses.FrozenInstanceError)):
            model.metadata["x"] = 1
        with self.assertRaises(ValueError):
            AnalysisProvenance.from_dict({**model.to_dict(), "created_by": " "})
        with self.assertRaises(ValueError):
            AnalysisProvenance.from_dict({**model.to_dict(), "metadata": {"token": "x"}})

    def test_capabilities_are_declarations_and_round_trip(self):
        model = capabilities(supports_market_gap=False)
        self.assertFalse(model.supports_market_gap)
        self.assertEqual(AnalysisCapabilities.from_dict(model.to_dict()), model)
        with self.assertRaises(TypeError):
            capabilities(supports_severity=1)

    def test_evidence_zero_round_trip_and_deep_freeze(self):
        model = evidence()
        self.assertEqual(model.measured_value, 0.0)
        self.assertEqual(RealityGapEvidenceReference.from_dict(model.to_dict()), model)
        self.assertIsInstance(model.metadata["rank"], tuple)

    def test_unavailable_evidence_preserves_none(self):
        model = evidence(measured_value=None, availability="MISSING")
        self.assertIsNone(model.measured_value)
        with self.assertRaises(ValueError):
            evidence(measured_value=0.0, availability="MISSING")

    def test_ineligible_evidence_requires_rejection_reason(self):
        with self.assertRaises(ValueError):
            evidence(eligibility=RealityGapEvidenceEligibility.INELIGIBLE)
        model = evidence(eligibility=RealityGapEvidenceEligibility.INELIGIBLE,
                         rejection_reason="outside eligible window")
        self.assertEqual(model.rejection_reason, "outside eligible window")
        with self.assertRaises(ValueError):
            evidence(rejection_reason="not allowed")

    def test_naive_evidence_time_and_boolean_metrics_rejected(self):
        data = evidence().to_dict()
        data["observed_at"] = "2026-07-15T12:00:00"
        with self.assertRaises(ValueError):
            RealityGapEvidenceReference.from_dict(data)
        data = evidence().to_dict()
        data["quality"] = True
        with self.assertRaises(TypeError):
            RealityGapEvidenceReference.from_dict(data)

    def test_observability_record_validates_counts_and_coverage(self):
        model = ObservabilityGapRecord(
            ObservabilityGapType.LOW_COVERAGE, "funding", "STALE", 4, 2, 50.0, 70.0,
            ("confirmation",), ("ev-1",), "Only half the expected samples were eligible.", {},
        )
        self.assertEqual(ObservabilityGapRecord.from_dict(model.to_dict()), model)
        with self.assertRaises(ValueError):
            dataclasses.replace(model, measured_count=5)
        with self.assertRaises(ValueError):
            dataclasses.replace(model, coverage_ratio=101)
        with self.assertRaises(ValueError):
            dataclasses.replace(model, evidence_refs=("ev-1", "ev-1"))

    def test_explanation_gap_validates_without_calculation(self):
        model = ExplanationGapRecord(20.0, 1, 2, 1, ("c1",), ("limited",), "Residual facts.", "v1", {})
        self.assertEqual(ExplanationGapRecord.from_dict(model.to_dict()), model)
        with self.assertRaises(ValueError):
            dataclasses.replace(model, conflicting_candidate_count=-1)
        with self.assertRaises(ValueError):
            dataclasses.replace(model, unexplained_residual_score=101)

    def test_candidate_round_trip_and_optional_metrics(self):
        model = candidate()
        self.assertEqual(RootCauseCandidate.from_dict(model.to_dict()), model)
        optional = dataclasses.replace(model, confidence=None, temporal_precedence=None,
                                       direct_relevance=None, evidence_coverage=None)
        self.assertIsNone(optional.confidence)

    def test_rejected_candidate_contract(self):
        with self.assertRaises(ValueError):
            candidate(disposition=RootCauseDisposition.REJECTED,
                      role=RootCauseRole.REJECTED_CANDIDATE)
        model = candidate(disposition=RootCauseDisposition.REJECTED,
                          role=RootCauseRole.REJECTED_CANDIDATE,
                          rejection_reason="contradicted")
        self.assertEqual(model.disposition, RootCauseDisposition.REJECTED)
        with self.assertRaises(ValueError):
            candidate(rejection_reason="invalid")

    def test_candidate_self_and_duplicate_references_rejected(self):
        with self.assertRaises(ValueError):
            candidate(parent="candidate-1")
        with self.assertRaises(ValueError):
            candidate(children=("candidate-1",))
        with self.assertRaises(ValueError):
            candidate(alternatives=("candidate-1",))
        with self.assertRaises(ValueError):
            candidate(refs=("ev-1", "ev-1"))


class TreeTests(unittest.TestCase):
    def test_valid_multi_root_tree_and_deterministic_edges(self):
        first = candidate("a", children=("b",))
        second = candidate("b", parent="a")
        third = candidate("c")
        model = tree(("a", "b", "c"), ("a", "c"), ("a", "b", "c"),
                     edges=(("a", "b"),), maximum_depth=2)
        validate_root_cause_tree(model, (first, second, third))
        self.assertEqual(RootCauseTree.from_dict(model.to_dict()), model)

    def test_tree_rejects_missing_reference_duplicate_and_self_edge(self):
        with self.assertRaises(ValueError):
            tree(edges=(("candidate-1", "missing"),))
        with self.assertRaises(ValueError):
            tree(edges=(("candidate-1", "candidate-1"),))
        with self.assertRaises(ValueError):
            tree(("a", "b"), ("a",), ("a", "b"), edges=(("a", "b"), ("a", "b")), maximum_depth=2)

    def test_tree_rejects_cycle_multiple_parent_and_depth(self):
        with self.assertRaises(ValueError):
            tree(("a", "b"), ("a",), ("a", "b"), edges=(("a", "b"), ("b", "a")), maximum_depth=2)
        with self.assertRaises(ValueError):
            tree(("a", "b", "c"), ("a", "c"), ("a", "b", "c"), edges=(("a", "b"), ("c", "b")), maximum_depth=2)
        with self.assertRaises(ValueError):
            tree(("a", "b"), ("a",), ("a", "b"), edges=(("a", "b"),), maximum_depth=1)

    def test_tree_validates_dispositions_and_parent_child_agreement(self):
        model = tree(("a",), ("a",), accepted=(), rejected=(), unresolved=("a",))
        with self.assertRaises(ValueError):
            validate_root_cause_tree(model, (candidate("a"),))
        parent = candidate("a", children=())
        child = candidate("b", parent="a")
        model = tree(("a", "b"), ("a",), ("a", "b"), edges=(("a", "b"),), maximum_depth=2)
        with self.assertRaises(ValueError):
            validate_root_cause_tree(model, (parent, child))


class TraceAndAnalysisTests(unittest.TestCase):
    def test_trace_round_trip_and_window(self):
        model = trace()
        self.assertEqual(RealityGapDecisionTrace.from_dict(model.to_dict()), model)
        with self.assertRaises(ValueError):
            dataclasses.replace(model, eligible_window_start=NOW + timedelta(seconds=1))
        self.assertNotIn("reasoning", inspect.signature(RealityGapDecisionTrace).parameters)

    def test_valid_analysis_with_none_optional_metrics(self):
        model = analysis(
            knowledge_gap_score=None, explanation_confidence=None, severity=None,
            root_cause_tree=None, tree_version=None,
            analysis_capabilities=capabilities(
                supports_knowledge_gap_metric=False,
                supports_explanation_confidence_metric=False,
                supports_root_cause_tree=False, supports_severity=False,
            ),
        )
        self.assertEqual(model.asset, "BTC")
        self.assertIsNone(model.knowledge_gap_score)

    def test_full_analysis_round_trip(self):
        model = analysis()
        self.assertEqual(RealityGapAnalysis.from_dict(model.to_dict()), model)
        self.assertEqual(model.to_dict(), RealityGapAnalysis.from_dict(model.to_dict()).to_dict())

    def test_capability_false_requires_none_and_true_permits_value(self):
        with self.assertRaises(ValueError):
            analysis(analysis_capabilities=capabilities(supports_knowledge_gap_metric=False))
        with self.assertRaises(ValueError):
            analysis(analysis_capabilities=capabilities(supports_explanation_confidence_metric=False))
        with self.assertRaises(ValueError):
            analysis(analysis_capabilities=capabilities(supports_root_cause_tree=False))
        with self.assertRaises(ValueError):
            analysis(analysis_capabilities=capabilities(supports_severity=False))
        self.assertEqual(analysis().severity, RealityGapSeverity.MEDIUM)

    def test_versions_must_agree(self):
        with self.assertRaises(ValueError):
            analysis(analysis_policy_version="other")
        with self.assertRaises(ValueError):
            analysis(metric_version="other")
        with self.assertRaises(ValueError):
            analysis(taxonomy_version="other")
        with self.assertRaises(ValueError):
            analysis(tree_version="other")
        with self.assertRaises(ValueError):
            analysis(trace_version="other")

    def test_analysis_version_and_revision_reason(self):
        with self.assertRaises(ValueError):
            analysis(analysis_version=0)
        with self.assertRaises(ValueError):
            analysis(analysis_version=2)
        self.assertEqual(analysis(analysis_version=2, revision_reason="Policy correction.").analysis_version, 2)

    def test_unknown_dimension_exclusivity_and_group_integrity(self):
        with self.assertRaises(ValueError):
            analysis(dimensions=(RealityGapDimension.UNKNOWN, RealityGapDimension.MARKET))
        with self.assertRaises(ValueError):
            analysis(accepted_candidate_ids=("candidate-1",), unresolved_candidate_ids=("candidate-1",))
        with self.assertRaises(ValueError):
            analysis(accepted_candidate_ids=("missing",))

    def test_duplicate_evidence_and_unresolved_references_rejected(self):
        ev = evidence()
        with self.assertRaises(ValueError):
            analysis(supporting_evidence=(ev, ev))
        with self.assertRaises(ValueError):
            analysis(root_cause_candidates=(candidate(refs=("missing",)),))
        with self.assertRaises(ValueError):
            analysis(decision_trace=trace(considered=("missing",)))

    def test_considered_evidence_must_be_eligible_and_inside_window(self):
        ineligible = evidence(
            eligibility=RealityGapEvidenceEligibility.INELIGIBLE,
            rejection_reason="outside window",
        )
        with self.assertRaises(ValueError):
            analysis(supporting_evidence=(ineligible,))
        late = dataclasses.replace(evidence(), observed_at=NOW + timedelta(seconds=1))
        with self.assertRaises(ValueError):
            analysis(supporting_evidence=(late,))

    def test_source_timeline_versions_and_entry_ids(self):
        with self.assertRaises(ValueError):
            analysis(source_timeline_versions=())
        with self.assertRaises(ValueError):
            analysis(source_timeline_versions=(1, 1))
        with self.assertRaises(ValueError):
            analysis(source_timeline_versions=(0,))
        with self.assertRaises(ValueError):
            analysis(source_entry_ids=())

    def test_input_collections_unchanged_and_metadata_frozen(self):
        source = {"labels": ["baseline"]}
        model = analysis(metadata=source)
        self.assertEqual(source, {"labels": ["baseline"]})
        source["labels"].append("later")
        self.assertEqual(model.metadata["labels"], ("baseline",))
        with self.assertRaises(TypeError):
            model.metadata["x"] = 1

    def test_deterministic_serialization_and_mapping_order(self):
        first = analysis(metadata={"b": 2, "a": 1})
        second = analysis(metadata={"a": 1, "b": 2})
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(canonical_json_bytes(first), canonical_json_bytes(second))
        self.assertEqual(canonical_json_bytes(first), canonical_json_bytes(first))

    def test_forbidden_domain_fields_absent(self):
        fields = set(inspect.signature(RealityGapAnalysis).parameters)
        for forbidden in ("trade", "direction", "execution", "learning", "outcome"):
            self.assertNotIn(forbidden, fields)
        module_source = inspect.getsource(RealityGapAnalysis)
        self.assertNotIn("calculate_", module_source)
        self.assertNotIn("classify_", module_source)


class RevisionTests(unittest.TestCase):
    def test_valid_revision(self):
        previous = analysis()
        current = analysis(analysis_version=2, revision_reason="Corrected declared disposition.")
        validate_analysis_revision(previous, current)
        self.assertEqual(previous.analysis_version, 1)

    def test_revision_identity_and_version_mismatch(self):
        previous = analysis()
        with self.assertRaises(ValueError):
            validate_analysis_revision(previous, analysis(gap_id="other", analysis_version=2, revision_reason="x"))
        with self.assertRaises(ValueError):
            validate_analysis_revision(previous, analysis(analysis_version=3, revision_reason="x"))

    def test_revision_rejects_boundary_expansion(self):
        previous = analysis()
        with self.assertRaises(ValueError):
            validate_analysis_revision(previous, analysis(
                analysis_version=2, revision_reason="x", source_timeline_versions=(1, 2)))
        with self.assertRaises(ValueError):
            validate_analysis_revision(previous, analysis(
                analysis_version=2, revision_reason="x", source_entry_ids=("entry-1", "entry-2")))
        shifted_trace = dataclasses.replace(trace(), eligible_window_end=NOW + timedelta(seconds=1))
        with self.assertRaises(ValueError):
            validate_analysis_revision(previous, analysis(
                analysis_version=2, revision_reason="x", decision_trace=shifted_trace))
        new_evidence = dataclasses.replace(evidence(), evidence_id="ev-2")
        new_candidate = dataclasses.replace(candidate(), supporting_evidence_refs=("ev-2",))
        new_trace = dataclasses.replace(trace(), evidence_considered=("ev-2",))
        with self.assertRaises(ValueError):
            validate_analysis_revision(previous, analysis(
                analysis_version=2, revision_reason="x",
                supporting_evidence=(new_evidence,), root_cause_candidates=(new_candidate,),
                decision_trace=new_trace))


if __name__ == "__main__":
    unittest.main()
