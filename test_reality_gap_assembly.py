"""Focused tests for deterministic Reality Gap assembly."""

import ast
import dataclasses
import inspect
from pathlib import Path
import unittest

from app.intelligence.reality_gap import (
    AnalysisCapabilities,
    RealityGapAssembler,
    RealityGapAssemblyInput,
    RealityGapAssemblyResult,
    RealityGapDimension,
    RealityGapEvidenceEligibility,
    RealityGapEvidenceType,
    RealityGapSeverity,
    RootCauseDisposition,
    RootCauseRole,
    canonical_json_bytes,
)
from test_reality_gap_contracts import (
    analysis as contract_analysis,
    candidate,
    capabilities,
    evidence,
    provenance,
    trace,
    tree,
)


def assembly_input(**changes):
    model = contract_analysis()
    values = dict(
        gap_id=model.gap_id,
        expectation_id=model.expectation_id,
        evaluation_id=model.evaluation_id,
        timeline_id=model.timeline_id,
        asset=model.asset,
        analysis_version=model.analysis_version,
        created_at=model.created_at,
        evaluated_at=model.evaluated_at,
        primary_type=model.primary_type,
        dimensions=model.dimensions,
        intelligence_gap_types=model.intelligence_gap_types,
        observability_gap_types=model.observability_gap_types,
        severity=model.severity,
        surprise_score=model.surprise_score,
        knowledge_gap_score=model.knowledge_gap_score,
        explanation_confidence=model.explanation_confidence,
        unexplained_residual_score=model.unexplained_residual_score,
        missing_expected_events=model.missing_expected_events,
        unexpected_events=model.unexpected_events,
        contradictory_events=model.contradictory_events,
        fulfilled_events=model.fulfilled_events,
        evidence=model.supporting_evidence,
        root_cause_candidates=model.root_cause_candidates,
        root_cause_tree=model.root_cause_tree,
        observability_gaps=model.observability_gaps,
        explanation_gap=model.explanation_gap,
        source_expectation_snapshot=model.source_expectation_snapshot,
        source_evaluation_snapshot=model.source_evaluation_snapshot,
        source_timeline_versions=model.source_timeline_versions,
        source_entry_ids=model.source_entry_ids,
        analysis_policy_version=model.analysis_policy_version,
        metric_version=model.metric_version,
        taxonomy_version=model.taxonomy_version,
        tree_version=model.tree_version,
        trace_version=model.trace_version,
        provenance=model.provenance,
        analysis_capabilities=model.analysis_capabilities,
        decision_trace=model.decision_trace,
        revision_reason=model.revision_reason,
        metadata=model.metadata,
    )
    values.update(changes)
    return RealityGapAssemblyInput(**values)


def without_tree_and_candidates(**changes):
    values = dict(
        root_cause_candidates=(),
        root_cause_tree=None,
        tree_version=None,
        analysis_capabilities=capabilities(
            supports_root_cause_candidates=False,
            supports_root_cause_tree=False,
        ),
    )
    values.update(changes)
    return assembly_input(**values)


class AssemblyModelTests(unittest.TestCase):
    def test_valid_assembly_input_is_immutable_and_round_trips(self):
        source = {"nested": ["value"]}
        model = assembly_input(metadata=source)
        source["nested"].append("later")
        self.assertEqual(model.metadata["nested"], ("value",))
        self.assertEqual(RealityGapAssemblyInput.from_dict(model.to_dict()), model)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            model.asset = "ETH"
        with self.assertRaises(TypeError):
            model.metadata["x"] = 1

    def test_assembly_result_is_immutable_and_round_trips(self):
        result = RealityGapAssembler().assemble(assembly_input())
        self.assertEqual(RealityGapAssemblyResult.from_dict(result.to_dict()), result)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.created_at = result.created_at
        with self.assertRaises(TypeError):
            result.metadata["x"] = 1
        with self.assertRaisesRegex(ValueError, "candidate groups"):
            dataclasses.replace(result, accepted_candidate_ids=())

    def test_input_objects_are_unchanged(self):
        model = assembly_input()
        before = model.to_dict()
        RealityGapAssembler().assemble(model)
        self.assertEqual(model.to_dict(), before)

    def test_no_automatic_ids_or_timestamps(self):
        model = assembly_input(gap_id="caller-gap")
        first = RealityGapAssembler().assemble(model)
        second = RealityGapAssembler().assemble(model)
        self.assertEqual(first.analysis.gap_id, "caller-gap")
        self.assertEqual(first.created_at, model.created_at)
        self.assertEqual(first, second)


class OrderingAndEvidenceTests(unittest.TestCase):
    def test_valid_assembly_and_evidence_sorted_by_id(self):
        ev_b = dataclasses.replace(evidence(), evidence_id="ev-b")
        ev_a = dataclasses.replace(evidence(), evidence_id="ev-a")
        cause = dataclasses.replace(candidate(), supporting_evidence_refs=("ev-a",))
        model = assembly_input(
            evidence=(ev_b, ev_a),
            root_cause_candidates=(cause,),
            root_cause_tree=None,
            tree_version=None,
            decision_trace=dataclasses.replace(trace(), evidence_considered=("ev-a",)),
        )
        result = RealityGapAssembler().assemble(model)
        self.assertEqual(tuple(item.evidence_id for item in result.analysis.supporting_evidence), ("ev-a", "ev-b"))
        self.assertEqual(result.eligible_evidence_ids, ("ev-a", "ev-b"))

    def test_candidates_sorted_by_id(self):
        cause_b = dataclasses.replace(candidate(), candidate_id="cause-b")
        cause_a = dataclasses.replace(candidate(), candidate_id="cause-a")
        model = assembly_input(
            root_cause_candidates=(cause_b, cause_a),
            root_cause_tree=None,
            tree_version=None,
        )
        result = RealityGapAssembler().assemble(model)
        self.assertEqual(tuple(item.candidate_id for item in result.analysis.root_cause_candidates), ("cause-a", "cause-b"))
        self.assertEqual(result.accepted_candidate_ids, ("cause-a", "cause-b"))

    def test_eligible_and_ineligible_evidence_are_both_preserved(self):
        eligible = dataclasses.replace(evidence(), evidence_id="eligible")
        ineligible = dataclasses.replace(
            evidence(), evidence_id="ineligible",
            eligibility=RealityGapEvidenceEligibility.INELIGIBLE,
            rejection_reason="outside eligible window",
        )
        model = assembly_input(
            evidence=(ineligible, eligible),
            root_cause_candidates=(dataclasses.replace(candidate(), supporting_evidence_refs=("eligible",)),),
            decision_trace=dataclasses.replace(
                trace(), evidence_considered=("eligible",), evidence_rejected=("ineligible",)
            ),
        )
        result = RealityGapAssembler().assemble(model)
        self.assertEqual(result.eligible_evidence_ids, ("eligible",))
        self.assertEqual(result.ineligible_evidence_ids, ("ineligible",))
        self.assertEqual(len(result.analysis.supporting_evidence), 2)

    def test_duplicate_evidence_and_candidate_ids_rejected(self):
        ev = evidence()
        with self.assertRaisesRegex(ValueError, "duplicate evidence"):
            RealityGapAssembler().assemble(assembly_input(evidence=(ev, ev)))
        cause = candidate()
        with self.assertRaisesRegex(ValueError, "duplicate candidate"):
            RealityGapAssembler().assemble(assembly_input(root_cause_candidates=(cause, cause)))

    def test_source_identity_and_lineage_references_validated(self):
        with self.assertRaisesRegex(ValueError, "expectation snapshot"):
            RealityGapAssembler().assemble(assembly_input(source_expectation_snapshot={"expectation_id": "other"}))
        with self.assertRaisesRegex(ValueError, "Timeline identity"):
            RealityGapAssembler().assemble(assembly_input(evidence=(dataclasses.replace(evidence(), timeline_id="other"),)))
        with self.assertRaisesRegex(ValueError, "entry ID"):
            RealityGapAssembler().assemble(assembly_input(evidence=(dataclasses.replace(evidence(), entry_id="other"),)))


class CandidateAndTreeTests(unittest.TestCase):
    def test_missing_candidate_evidence_reference_rejected(self):
        cause = dataclasses.replace(candidate(), supporting_evidence_refs=("missing",))
        with self.assertRaisesRegex(ValueError, "does not resolve"):
            RealityGapAssembler().assemble(assembly_input(root_cause_candidates=(cause,)))

    def test_accepted_candidate_requires_eligible_support(self):
        cause = dataclasses.replace(candidate(), supporting_evidence_refs=())
        with self.assertRaisesRegex(ValueError, "requires eligible"):
            RealityGapAssembler().assemble(assembly_input(root_cause_candidates=(cause,)))

    def test_accepted_candidate_with_ineligible_support_rejected(self):
        ineligible = dataclasses.replace(
            evidence(), eligibility=RealityGapEvidenceEligibility.INELIGIBLE,
            rejection_reason="outside eligible window",
        )
        model = assembly_input(
            evidence=(ineligible,),
            decision_trace=dataclasses.replace(trace(), evidence_considered=(), evidence_rejected=("ev-1",)),
        )
        with self.assertRaisesRegex(ValueError, "must be ELIGIBLE"):
            RealityGapAssembler().assemble(model)

    def test_rejected_and_unresolved_candidate_refs_preserved(self):
        ineligible = dataclasses.replace(
            evidence(), evidence_id="audit",
            eligibility=RealityGapEvidenceEligibility.INELIGIBLE,
            rejection_reason="outside eligible window",
        )
        accepted = dataclasses.replace(candidate(), candidate_id="accepted")
        rejected = candidate(
            "rejected", disposition=RootCauseDisposition.REJECTED,
            role=RootCauseRole.REJECTED_CANDIDATE, refs=("audit",),
            rejection_reason="evidence was ineligible",
        )
        unresolved = candidate(
            "unresolved", disposition=RootCauseDisposition.UNRESOLVED,
            role=RootCauseRole.ALTERNATIVE_CANDIDATE, refs=("audit",),
        )
        model = assembly_input(
            evidence=(evidence(), ineligible),
            root_cause_candidates=(unresolved, rejected, accepted),
            root_cause_tree=None,
            tree_version=None,
            decision_trace=dataclasses.replace(trace(), evidence_rejected=("audit",)),
        )
        result = RealityGapAssembler().assemble(model)
        self.assertEqual(result.accepted_candidate_ids, ("accepted",))
        self.assertEqual(result.rejected_candidate_ids, ("rejected",))
        self.assertEqual(result.unresolved_candidate_ids, ("unresolved",))
        by_id = {item.candidate_id: item for item in result.analysis.root_cause_candidates}
        self.assertEqual(by_id["rejected"].supporting_evidence_refs, ("audit",))
        self.assertEqual(by_id["unresolved"].supporting_evidence_refs, ("audit",))

    def test_unresolved_without_eligible_support_requires_limitation(self):
        ineligible = dataclasses.replace(
            evidence(), eligibility=RealityGapEvidenceEligibility.INELIGIBLE,
            rejection_reason="outside eligible window",
        )
        unresolved = dataclasses.replace(
            candidate(), disposition=RootCauseDisposition.UNRESOLVED,
            role=RootCauseRole.ALTERNATIVE_CANDIDATE, limitations=(),
        )
        model = assembly_input(
            evidence=(ineligible,), root_cause_candidates=(unresolved,),
            root_cause_tree=None, tree_version=None,
            decision_trace=dataclasses.replace(trace(), evidence_considered=(), evidence_rejected=("ev-1",)),
        )
        with self.assertRaisesRegex(ValueError, "requires a limitation"):
            RealityGapAssembler().assemble(model)

    def test_valid_tree_assembled_and_invalid_candidate_set_rejected(self):
        result = RealityGapAssembler().assemble(assembly_input())
        self.assertEqual(result.analysis.root_cause_tree, tree())
        extra = dataclasses.replace(candidate(), candidate_id="extra")
        with self.assertRaisesRegex(ValueError, "tree candidate IDs"):
            RealityGapAssembler().assemble(assembly_input(root_cause_candidates=(candidate(), extra)))


class CapabilityTests(unittest.TestCase):
    def test_candidates_and_tree_forbidden_when_unsupported(self):
        with self.assertRaisesRegex(ValueError, "candidates are unsupported"):
            RealityGapAssembler().assemble(assembly_input(
                analysis_capabilities=capabilities(supports_root_cause_candidates=False)
            ))
        with self.assertRaisesRegex(ValueError, "tree is unsupported"):
            RealityGapAssembler().assemble(assembly_input(
                analysis_capabilities=capabilities(supports_root_cause_tree=False)
            ))
        result = RealityGapAssembler().assemble(without_tree_and_candidates())
        self.assertEqual(result.analysis.root_cause_candidates, ())

    def test_market_dimension_forbidden_when_unsupported(self):
        model = assembly_input(analysis_capabilities=capabilities(supports_market_gap=False))
        with self.assertRaisesRegex(ValueError, "MARKET dimension"):
            RealityGapAssembler().assemble(model)

    def test_intelligence_gap_forbidden_when_unsupported(self):
        model = assembly_input(analysis_capabilities=capabilities(supports_intelligence_gap=False))
        with self.assertRaisesRegex(ValueError, "Intelligence Gap"):
            RealityGapAssembler().assemble(model)

    def test_observability_gap_forbidden_when_unsupported(self):
        model = assembly_input(
            observability_gap_types=("LOW_COVERAGE",),
            analysis_capabilities=capabilities(supports_observability_gap=False),
        )
        with self.assertRaisesRegex(ValueError, "Observability Gap"):
            RealityGapAssembler().assemble(model)

    def test_explanation_gap_forbidden_when_unsupported(self):
        model = assembly_input(analysis_capabilities=capabilities(supports_explanation_gap=False))
        with self.assertRaisesRegex(ValueError, "Explanation Gap"):
            RealityGapAssembler().assemble(model)

    def test_metric_and_severity_capability_consistency(self):
        with self.assertRaisesRegex(ValueError, "knowledge gap"):
            RealityGapAssembler().assemble(assembly_input(
                analysis_capabilities=capabilities(supports_knowledge_gap_metric=False)
            ))
        with self.assertRaisesRegex(ValueError, "severity"):
            RealityGapAssembler().assemble(assembly_input(
                analysis_capabilities=capabilities(supports_severity=False)
            ))
        with self.assertRaisesRegex(ValueError, "metric_version"):
            RealityGapAssembler().assemble(assembly_input(metric_version=None, provenance=provenance(metric=None)))
        with self.assertRaisesRegex(ValueError, "severity policy"):
            RealityGapAssembler().assemble(assembly_input(
                provenance=dataclasses.replace(provenance(), severity_policy_version=None)
            ))
        trace_with_unsupported_metric = dataclasses.replace(
            trace(), metric_outputs={"surprise": 55.0, "knowledge_gap_score": 10.0}
        )
        with self.assertRaisesRegex(ValueError, "Decision Trace"):
            RealityGapAssembler().assemble(assembly_input(
                knowledge_gap_score=None,
                analysis_capabilities=capabilities(supports_knowledge_gap_metric=False),
                decision_trace=trace_with_unsupported_metric,
            ))


class TraceTests(unittest.TestCase):
    def test_trace_considered_and_rejected_refs_resolve(self):
        with self.assertRaisesRegex(ValueError, "considered evidence"):
            RealityGapAssembler().assemble(assembly_input(
                decision_trace=dataclasses.replace(trace(), evidence_considered=("missing",))
            ))
        with self.assertRaisesRegex(ValueError, "rejected evidence"):
            RealityGapAssembler().assemble(assembly_input(
                decision_trace=dataclasses.replace(trace(), evidence_rejected=("missing",))
            ))

    def test_trace_overlap_is_rejected_by_input_contract(self):
        with self.assertRaisesRegex(ValueError, "must be disjoint"):
            dataclasses.replace(trace(), evidence_rejected=("ev-1",))

    def test_ineligible_considered_evidence_rejected(self):
        ineligible = dataclasses.replace(
            evidence(), eligibility=RealityGapEvidenceEligibility.INELIGIBLE,
            rejection_reason="outside eligible window",
        )
        model = without_tree_and_candidates(evidence=(ineligible,))
        with self.assertRaisesRegex(ValueError, "must not be considered"):
            RealityGapAssembler().assemble(model)

    def test_trace_severity_metric_and_policy_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "severity"):
            RealityGapAssembler().assemble(assembly_input(
                decision_trace=dataclasses.replace(trace(), severity_output=RealityGapSeverity.HIGH)
            ))
        with self.assertRaisesRegex(ValueError, "metric output"):
            RealityGapAssembler().assemble(assembly_input(
                decision_trace=dataclasses.replace(trace(), metric_outputs={"surprise_score": 1.0})
            ))
        with self.assertRaisesRegex(ValueError, "policy version"):
            RealityGapAssembler().assemble(assembly_input(
                decision_trace=dataclasses.replace(trace(), policy_versions={"taxonomy_version": "other"})
            ))


class WarningAndReproducibilityTests(unittest.TestCase):
    def test_no_eligible_and_ineligible_audit_warnings(self):
        ineligible = dataclasses.replace(
            evidence(), eligibility=RealityGapEvidenceEligibility.INELIGIBLE,
            rejection_reason="outside eligible window",
        )
        model = without_tree_and_candidates(
            evidence=(ineligible,),
            decision_trace=dataclasses.replace(trace(), evidence_considered=(), evidence_rejected=("ev-1",)),
        )
        result = RealityGapAssembler().assemble(model)
        self.assertIn("no eligible evidence supplied", result.warnings)
        self.assertIn("analysis contains ineligible audit evidence", result.warnings)

    def test_supported_but_empty_candidate_and_tree_warnings(self):
        result = RealityGapAssembler().assemble(assembly_input(
            root_cause_candidates=(), root_cause_tree=None, tree_version=None
        ))
        self.assertIn("no Root Cause Candidate supplied despite supported capability", result.warnings)
        self.assertIn("tree capability supported but tree omitted", result.warnings)

    def test_only_observability_and_optional_explanation_warnings(self):
        observation = dataclasses.replace(evidence(), evidence_type=RealityGapEvidenceType.OBSERVABILITY_FACT)
        result = RealityGapAssembler().assemble(assembly_input(
            evidence=(observation,), explanation_gap=None
        ))
        self.assertIn("only observability evidence is available", result.warnings)
        self.assertIn("optional explanation gap omitted", result.warnings)

    def test_warnings_and_assembly_trace_are_deterministic(self):
        model = assembly_input(root_cause_candidates=(), root_cause_tree=None, tree_version=None)
        first = RealityGapAssembler().assemble(model)
        second = RealityGapAssembler().assemble(model)
        self.assertEqual(first.warnings, second.warnings)
        self.assertEqual(first.assembly_trace, second.assembly_trace)
        self.assertEqual(first.assembly_trace[-1], "canonical serialization verified")

    def test_canonical_bytes_and_mapping_order_reproducible(self):
        first = assembly_input(metadata={"b": 2, "a": 1})
        second = assembly_input(metadata={"a": 1, "b": 2})
        result_first = RealityGapAssembler().assemble(first)
        result_second = RealityGapAssembler().assemble(second)
        self.assertEqual(result_first, result_second)
        self.assertEqual(canonical_json_bytes(result_first), canonical_json_bytes(result_second))


class RevisionAndBoundaryTests(unittest.TestCase):
    def test_valid_revision_assembly(self):
        assembler = RealityGapAssembler()
        previous = assembler.assemble(assembly_input()).analysis
        result = assembler.assemble_revision(previous, assembly_input(
            analysis_version=2, revision_reason="Corrected declared audit facts."
        ))
        self.assertEqual(result.analysis.analysis_version, 2)

    def test_revision_boundary_expansion_and_version_jump_rejected(self):
        assembler = RealityGapAssembler()
        previous = assembler.assemble(assembly_input()).analysis
        with self.assertRaisesRegex(ValueError, "later Timeline versions"):
            assembler.assemble_revision(previous, assembly_input(
                analysis_version=2, revision_reason="Expanded boundary.",
                source_timeline_versions=(1, 2),
            ))
        with self.assertRaisesRegex(ValueError, "increment by one"):
            assembler.assemble_revision(previous, assembly_input(
                analysis_version=3, revision_reason="Jumped version."
            ))

    def test_runtime_has_no_analytical_methods(self):
        source = inspect.getsource(RealityGapAssembler)
        for forbidden in (
            "calculate_metric", "classify_gap", "generate_candidate", "extract_evidence",
            "random", "uuid", "datetime.now",
        ):
            self.assertNotIn(forbidden, source)

    def test_dependency_boundary(self):
        path = Path("app/intelligence/reality_gap/assembly.py")
        tree_node = ast.parse(path.read_text())
        allowed = {"dataclasses", "datetime", "typing"}
        for node in ast.walk(tree_node):
            if isinstance(node, ast.Import):
                self.assertTrue(all(alias.name.split(".")[0] in allowed for alias in node.names))
            if isinstance(node, ast.ImportFrom) and node.level == 0:
                self.assertIn((node.module or "").split(".")[0], allowed)


if __name__ == "__main__":
    unittest.main()
