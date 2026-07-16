"""Deterministic assembly of already-prepared Reality Gap contracts.

This module validates and assembles declared inputs.  It deliberately contains
no evidence extraction, classification, candidate generation, or metric logic.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Mapping, Optional, Tuple

from .enums import (
    IntelligenceGapType,
    ObservabilityGapType,
    RealityGapDimension,
    RealityGapEvidenceEligibility,
    RealityGapEvidenceType,
    RealityGapPrimaryType,
    RealityGapSeverity,
    RootCauseDisposition,
)
from .models import (
    AnalysisCapabilities,
    AnalysisProvenance,
    ExplanationGapRecord,
    ObservabilityGapRecord,
    RealityGapAnalysis,
    RealityGapDecisionTrace,
    RealityGapEvidenceReference,
    RootCauseCandidate,
    validate_analysis_revision,
)
from .tree import RootCauseTree, validate_root_cause_tree
from .validation import (
    canonical_json_bytes,
    enum_tuple,
    enum_value,
    frozen_mapping,
    mapping_payload,
    optional_percentage,
    optional_text,
    parse_datetime,
    percentage,
    plain,
    positive_integer,
    positive_integer_tuple,
    required_text,
    text_tuple,
    typed_tuple,
    utc_datetime,
)


_WARNING_POLICY_ORDER = (
    "no eligible evidence supplied",
    "no Root Cause Candidate supplied despite supported capability",
    "knowledge gap metric intentionally unavailable",
    "explanation confidence metric intentionally unavailable",
    "tree capability supported but tree omitted",
    "only observability evidence is available",
    "optional explanation gap omitted",
    "analysis contains ineligible audit evidence",
    "ineligible audit evidence is not listed as rejected in Decision Trace",
)


def _unique_by_id(items: Tuple[Any, ...], attribute: str, label: str) -> Dict[str, Any]:
    indexed = {}
    for item in items:
        item_id = getattr(item, attribute)
        if item_id in indexed:
            raise ValueError("duplicate {0} ID: {1}".format(label, item_id))
        indexed[item_id] = item
    return indexed


def _ordered_warnings(values: Tuple[str, ...]) -> Tuple[str, ...]:
    ranks = {warning: index for index, warning in enumerate(_WARNING_POLICY_ORDER)}
    return tuple(sorted(set(values), key=lambda value: (ranks.get(value, len(ranks)), value)))


@dataclass(frozen=True)
class RealityGapAssemblyInput:
    gap_id: str
    expectation_id: str
    evaluation_id: str
    timeline_id: str
    asset: str
    analysis_version: int
    created_at: datetime
    evaluated_at: datetime
    primary_type: RealityGapPrimaryType
    dimensions: Tuple[RealityGapDimension, ...]
    intelligence_gap_types: Tuple[IntelligenceGapType, ...]
    observability_gap_types: Tuple[ObservabilityGapType, ...]
    severity: Optional[RealityGapSeverity]
    surprise_score: float
    knowledge_gap_score: Optional[float]
    explanation_confidence: Optional[float]
    unexplained_residual_score: Optional[float]
    missing_expected_events: Tuple[str, ...]
    unexpected_events: Tuple[str, ...]
    contradictory_events: Tuple[str, ...]
    fulfilled_events: Tuple[str, ...]
    evidence: Tuple[RealityGapEvidenceReference, ...]
    root_cause_candidates: Tuple[RootCauseCandidate, ...]
    root_cause_tree: Optional[RootCauseTree]
    observability_gaps: Tuple[ObservabilityGapRecord, ...]
    explanation_gap: Optional[ExplanationGapRecord]
    source_expectation_snapshot: Mapping[str, Any]
    source_evaluation_snapshot: Mapping[str, Any]
    source_timeline_versions: Tuple[int, ...]
    source_entry_ids: Tuple[str, ...]
    analysis_policy_version: str
    metric_version: Optional[str]
    taxonomy_version: str
    tree_version: Optional[str]
    trace_version: str
    provenance: AnalysisProvenance
    analysis_capabilities: AnalysisCapabilities
    decision_trace: RealityGapDecisionTrace
    revision_reason: Optional[str]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("gap_id", "expectation_id", "evaluation_id", "timeline_id"):
            object.__setattr__(self, name, required_text(getattr(self, name), name))
        object.__setattr__(self, "asset", required_text(self.asset, "asset").upper())
        version = positive_integer(self.analysis_version, "analysis_version")
        object.__setattr__(self, "analysis_version", version)
        created_at = utc_datetime(self.created_at, "created_at")
        evaluated_at = utc_datetime(self.evaluated_at, "evaluated_at")
        if created_at < evaluated_at:
            raise ValueError("created_at must not be before evaluated_at")
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "evaluated_at", evaluated_at)
        object.__setattr__(self, "primary_type", enum_value(self.primary_type, RealityGapPrimaryType, "primary_type"))
        dimensions = enum_tuple(self.dimensions, RealityGapDimension, "dimensions", required=True)
        if RealityGapDimension.UNKNOWN in dimensions and len(dimensions) > 1:
            raise ValueError("UNKNOWN dimension cannot coexist with specific dimensions")
        object.__setattr__(self, "dimensions", dimensions)
        object.__setattr__(self, "intelligence_gap_types", enum_tuple(self.intelligence_gap_types, IntelligenceGapType, "intelligence_gap_types"))
        object.__setattr__(self, "observability_gap_types", enum_tuple(self.observability_gap_types, ObservabilityGapType, "observability_gap_types"))
        if self.severity is not None:
            object.__setattr__(self, "severity", enum_value(self.severity, RealityGapSeverity, "severity"))
        object.__setattr__(self, "surprise_score", percentage(self.surprise_score, "surprise_score"))
        for name in ("knowledge_gap_score", "explanation_confidence", "unexplained_residual_score"):
            object.__setattr__(self, name, optional_percentage(getattr(self, name), name))
        for name in ("missing_expected_events", "unexpected_events", "contradictory_events", "fulfilled_events"):
            object.__setattr__(self, name, text_tuple(getattr(self, name), name))
        object.__setattr__(self, "evidence", typed_tuple(self.evidence, RealityGapEvidenceReference, "evidence"))
        object.__setattr__(self, "root_cause_candidates", typed_tuple(self.root_cause_candidates, RootCauseCandidate, "root_cause_candidates"))
        if self.root_cause_tree is not None and not isinstance(self.root_cause_tree, RootCauseTree):
            raise TypeError("root_cause_tree must be a RootCauseTree")
        object.__setattr__(self, "observability_gaps", typed_tuple(self.observability_gaps, ObservabilityGapRecord, "observability_gaps"))
        if self.explanation_gap is not None and not isinstance(self.explanation_gap, ExplanationGapRecord):
            raise TypeError("explanation_gap must be an ExplanationGapRecord")
        object.__setattr__(self, "source_expectation_snapshot", frozen_mapping(self.source_expectation_snapshot, "source_expectation_snapshot"))
        object.__setattr__(self, "source_evaluation_snapshot", frozen_mapping(self.source_evaluation_snapshot, "source_evaluation_snapshot"))
        object.__setattr__(self, "source_timeline_versions", positive_integer_tuple(self.source_timeline_versions, "source_timeline_versions", required=True))
        object.__setattr__(self, "source_entry_ids", text_tuple(self.source_entry_ids, "source_entry_ids", required=True))
        for name in ("analysis_policy_version", "taxonomy_version", "trace_version"):
            object.__setattr__(self, name, required_text(getattr(self, name), name))
        object.__setattr__(self, "metric_version", optional_text(self.metric_version, "metric_version"))
        object.__setattr__(self, "tree_version", optional_text(self.tree_version, "tree_version"))
        if not isinstance(self.provenance, AnalysisProvenance):
            raise TypeError("provenance must be AnalysisProvenance")
        if not isinstance(self.analysis_capabilities, AnalysisCapabilities):
            raise TypeError("analysis_capabilities must be AnalysisCapabilities")
        if not isinstance(self.decision_trace, RealityGapDecisionTrace):
            raise TypeError("decision_trace must be RealityGapDecisionTrace")
        revision_reason = optional_text(self.revision_reason, "revision_reason")
        if version > 1 and revision_reason is None:
            raise ValueError("analysis version greater than 1 requires revision_reason")
        object.__setattr__(self, "revision_reason", revision_reason)
        object.__setattr__(self, "metadata", frozen_mapping(self.metadata))

    def to_dict(self) -> dict:
        payload = plain(self.__dict__)
        payload["evidence"] = [item.to_dict() for item in self.evidence]
        payload["root_cause_candidates"] = [item.to_dict() for item in self.root_cause_candidates]
        payload["root_cause_tree"] = None if self.root_cause_tree is None else self.root_cause_tree.to_dict()
        payload["observability_gaps"] = [item.to_dict() for item in self.observability_gaps]
        payload["explanation_gap"] = None if self.explanation_gap is None else self.explanation_gap.to_dict()
        payload["provenance"] = self.provenance.to_dict()
        payload["analysis_capabilities"] = self.analysis_capabilities.to_dict()
        payload["decision_trace"] = self.decision_trace.to_dict()
        return payload

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RealityGapAssemblyInput":
        data = mapping_payload(value, cls.__name__)
        for name in ("created_at", "evaluated_at"):
            data[name] = parse_datetime(data[name], name)
        data["evidence"] = tuple(RealityGapEvidenceReference.from_dict(item) for item in data["evidence"])
        data["root_cause_candidates"] = tuple(RootCauseCandidate.from_dict(item) for item in data["root_cause_candidates"])
        data["root_cause_tree"] = None if data["root_cause_tree"] is None else RootCauseTree.from_dict(data["root_cause_tree"])
        data["observability_gaps"] = tuple(ObservabilityGapRecord.from_dict(item) for item in data["observability_gaps"])
        data["explanation_gap"] = None if data["explanation_gap"] is None else ExplanationGapRecord.from_dict(data["explanation_gap"])
        data["provenance"] = AnalysisProvenance.from_dict(data["provenance"])
        data["analysis_capabilities"] = AnalysisCapabilities.from_dict(data["analysis_capabilities"])
        data["decision_trace"] = RealityGapDecisionTrace.from_dict(data["decision_trace"])
        return cls(**data)


@dataclass(frozen=True)
class RealityGapAssemblyResult:
    analysis: RealityGapAnalysis
    eligible_evidence_ids: Tuple[str, ...]
    ineligible_evidence_ids: Tuple[str, ...]
    accepted_candidate_ids: Tuple[str, ...]
    rejected_candidate_ids: Tuple[str, ...]
    unresolved_candidate_ids: Tuple[str, ...]
    warnings: Tuple[str, ...]
    assembly_trace: Tuple[str, ...]
    created_at: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.analysis, RealityGapAnalysis):
            raise TypeError("analysis must be a RealityGapAnalysis")
        for name in (
            "eligible_evidence_ids", "ineligible_evidence_ids", "accepted_candidate_ids",
            "rejected_candidate_ids", "unresolved_candidate_ids", "warnings", "assembly_trace",
        ):
            object.__setattr__(self, name, text_tuple(getattr(self, name), name))
        expected_eligible = tuple(
            item.evidence_id for item in self.analysis.supporting_evidence
            if item.eligibility == RealityGapEvidenceEligibility.ELIGIBLE
        )
        expected_ineligible = tuple(
            item.evidence_id for item in self.analysis.supporting_evidence
            if item.eligibility == RealityGapEvidenceEligibility.INELIGIBLE
        )
        if self.eligible_evidence_ids != expected_eligible or self.ineligible_evidence_ids != expected_ineligible:
            raise ValueError("assembly result evidence groups must agree with analysis")
        if (
            self.accepted_candidate_ids != self.analysis.accepted_candidate_ids
            or self.rejected_candidate_ids != self.analysis.rejected_candidate_ids
            or self.unresolved_candidate_ids != self.analysis.unresolved_candidate_ids
        ):
            raise ValueError("assembly result candidate groups must agree with analysis")
        created_at = utc_datetime(self.created_at, "created_at")
        if created_at != self.analysis.created_at:
            raise ValueError("assembly result created_at must agree with analysis")
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "metadata", frozen_mapping(self.metadata))

    def to_dict(self) -> dict:
        payload = plain(self.__dict__)
        payload["analysis"] = self.analysis.to_dict()
        return payload

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RealityGapAssemblyResult":
        data = mapping_payload(value, cls.__name__)
        data["analysis"] = RealityGapAnalysis.from_dict(data["analysis"])
        data["created_at"] = parse_datetime(data["created_at"], "created_at")
        return cls(**data)


class RealityGapAssembler:
    """Validate and assemble already-interpreted Reality Gap inputs."""

    def assemble(self, assembly_input: RealityGapAssemblyInput) -> RealityGapAssemblyResult:
        if not isinstance(assembly_input, RealityGapAssemblyInput):
            raise TypeError("assembly_input must be a RealityGapAssemblyInput")

        self._validate_source_identity(assembly_input)
        evidence_by_id = _unique_by_id(assembly_input.evidence, "evidence_id", "evidence")
        candidate_by_id = _unique_by_id(assembly_input.root_cause_candidates, "candidate_id", "candidate")
        evidence = tuple(sorted(evidence_by_id.values(), key=lambda item: item.evidence_id))
        candidates = tuple(sorted(candidate_by_id.values(), key=lambda item: item.candidate_id))
        observability_gaps = tuple(sorted(
            assembly_input.observability_gaps,
            key=lambda item: (item.gap_type.value, item.subject),
        ))
        eligible_ids = tuple(item.evidence_id for item in evidence if item.eligibility == RealityGapEvidenceEligibility.ELIGIBLE)
        ineligible_ids = tuple(item.evidence_id for item in evidence if item.eligibility == RealityGapEvidenceEligibility.INELIGIBLE)

        self._validate_candidate_references(candidates, evidence_by_id)
        accepted_ids, rejected_ids, unresolved_ids = self._group_candidates(candidates)
        if assembly_input.root_cause_tree is not None:
            validate_root_cause_tree(assembly_input.root_cause_tree, candidates)
        self._validate_trace(assembly_input, evidence_by_id)
        self._validate_capabilities(assembly_input)
        self._validate_optional_outputs(assembly_input)

        analysis = RealityGapAnalysis(
            gap_id=assembly_input.gap_id,
            expectation_id=assembly_input.expectation_id,
            evaluation_id=assembly_input.evaluation_id,
            timeline_id=assembly_input.timeline_id,
            asset=assembly_input.asset,
            analysis_version=assembly_input.analysis_version,
            created_at=assembly_input.created_at,
            evaluated_at=assembly_input.evaluated_at,
            primary_type=assembly_input.primary_type,
            dimensions=assembly_input.dimensions,
            intelligence_gap_types=assembly_input.intelligence_gap_types,
            observability_gap_types=assembly_input.observability_gap_types,
            severity=assembly_input.severity,
            surprise_score=assembly_input.surprise_score,
            knowledge_gap_score=assembly_input.knowledge_gap_score,
            explanation_confidence=assembly_input.explanation_confidence,
            unexplained_residual_score=assembly_input.unexplained_residual_score,
            missing_expected_events=assembly_input.missing_expected_events,
            unexpected_events=assembly_input.unexpected_events,
            contradictory_events=assembly_input.contradictory_events,
            fulfilled_events=assembly_input.fulfilled_events,
            root_cause_candidates=candidates,
            root_cause_tree=assembly_input.root_cause_tree,
            accepted_candidate_ids=accepted_ids,
            rejected_candidate_ids=rejected_ids,
            unresolved_candidate_ids=unresolved_ids,
            supporting_evidence=evidence,
            observability_gaps=observability_gaps,
            explanation_gap=assembly_input.explanation_gap,
            source_expectation_snapshot=assembly_input.source_expectation_snapshot,
            source_evaluation_snapshot=assembly_input.source_evaluation_snapshot,
            source_timeline_versions=assembly_input.source_timeline_versions,
            source_entry_ids=assembly_input.source_entry_ids,
            analysis_policy_version=assembly_input.analysis_policy_version,
            metric_version=assembly_input.metric_version,
            taxonomy_version=assembly_input.taxonomy_version,
            tree_version=assembly_input.tree_version,
            trace_version=assembly_input.trace_version,
            provenance=assembly_input.provenance,
            analysis_capabilities=assembly_input.analysis_capabilities,
            decision_trace=assembly_input.decision_trace,
            revision_reason=assembly_input.revision_reason,
            metadata=assembly_input.metadata,
        )
        serialized = canonical_json_bytes(analysis)
        restored = RealityGapAnalysis.from_dict(analysis.to_dict())
        if restored != analysis or canonical_json_bytes(restored) != serialized:
            raise ValueError("analysis canonical serialization is not reproducible")

        warnings = self._warnings(assembly_input, evidence, eligible_ids, ineligible_ids, candidates)
        assembly_trace = (
            "source identity validated",
            "{0} evidence references indexed".format(len(evidence)),
            "{0} eligible and {1} ineligible evidence references preserved".format(len(eligible_ids), len(ineligible_ids)),
            "candidate references resolved",
            "candidate dispositions grouped",
            "Root Cause Tree {0}".format("validated" if assembly_input.root_cause_tree is not None else "omitted"),
            "Decision Trace validated",
            "capability consistency validated",
            "analysis constructed",
            "canonical serialization verified",
        )
        result = RealityGapAssemblyResult(
            analysis=analysis,
            eligible_evidence_ids=eligible_ids,
            ineligible_evidence_ids=ineligible_ids,
            accepted_candidate_ids=accepted_ids,
            rejected_candidate_ids=rejected_ids,
            unresolved_candidate_ids=unresolved_ids,
            warnings=warnings,
            assembly_trace=assembly_trace,
            created_at=assembly_input.created_at,
            metadata={"serialization_version": assembly_input.provenance.serialization_version},
        )
        if RealityGapAssemblyResult.from_dict(result.to_dict()) != result:
            raise ValueError("assembly result serialization is not reproducible")
        return result

    def assemble_revision(
        self,
        previous: RealityGapAnalysis,
        assembly_input: RealityGapAssemblyInput,
    ) -> RealityGapAssemblyResult:
        result = self.assemble(assembly_input)
        validate_analysis_revision(previous, result.analysis)
        return result

    @staticmethod
    def _validate_source_identity(value: RealityGapAssemblyInput) -> None:
        expectation_snapshot_id = value.source_expectation_snapshot.get("expectation_id")
        if expectation_snapshot_id is not None and expectation_snapshot_id != value.expectation_id:
            raise ValueError("source expectation snapshot identity mismatch")
        evaluation_snapshot_id = value.source_evaluation_snapshot.get("evaluation_id")
        if evaluation_snapshot_id is not None and evaluation_snapshot_id != value.evaluation_id:
            raise ValueError("source evaluation snapshot identity mismatch")
        evaluation_timeline_id = value.source_evaluation_snapshot.get("timeline_id")
        if evaluation_timeline_id is not None and evaluation_timeline_id != value.timeline_id:
            raise ValueError("source evaluation Timeline identity mismatch")
        source_versions = set(value.source_timeline_versions)
        source_entries = set(value.source_entry_ids)
        for item in value.evidence:
            if item.timeline_id != value.timeline_id:
                raise ValueError("evidence Timeline identity mismatch")
            if item.timeline_version not in source_versions:
                raise ValueError("evidence Timeline version is outside declared sources")
            if item.entry_id is not None and item.entry_id not in source_entries:
                raise ValueError("evidence entry ID is outside declared sources")

    @staticmethod
    def _validate_candidate_references(
        candidates: Tuple[RootCauseCandidate, ...],
        evidence_by_id: Mapping[str, RealityGapEvidenceReference],
    ) -> None:
        known = set(evidence_by_id)
        for item in candidates:
            references = item.supporting_evidence_refs + item.contradicting_evidence_refs
            if not set(references) <= known:
                raise ValueError("candidate evidence reference does not resolve: {0}".format(item.candidate_id))
            if item.disposition in (RootCauseDisposition.ACCEPTED, RootCauseDisposition.PARTIALLY_SUPPORTED):
                if not item.supporting_evidence_refs:
                    raise ValueError("accepted candidate requires eligible supporting evidence")
                if any(evidence_by_id[reference].eligibility != RealityGapEvidenceEligibility.ELIGIBLE for reference in item.supporting_evidence_refs):
                    raise ValueError("accepted candidate support must be ELIGIBLE")
            if item.disposition == RootCauseDisposition.UNRESOLVED:
                has_eligible_support = any(
                    evidence_by_id[reference].eligibility == RealityGapEvidenceEligibility.ELIGIBLE
                    for reference in item.supporting_evidence_refs
                )
                if not has_eligible_support and not item.limitations:
                    raise ValueError("unresolved candidate without eligible support requires a limitation")

    @staticmethod
    def _group_candidates(
        candidates: Tuple[RootCauseCandidate, ...],
    ) -> Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
        accepted = []
        rejected = []
        unresolved = []
        for item in candidates:
            if item.disposition in (RootCauseDisposition.ACCEPTED, RootCauseDisposition.PARTIALLY_SUPPORTED):
                accepted.append(item.candidate_id)
            elif item.disposition == RootCauseDisposition.REJECTED:
                rejected.append(item.candidate_id)
            elif item.disposition == RootCauseDisposition.UNRESOLVED:
                unresolved.append(item.candidate_id)
        return tuple(sorted(accepted)), tuple(sorted(rejected)), tuple(sorted(unresolved))

    @staticmethod
    def _validate_trace(
        value: RealityGapAssemblyInput,
        evidence_by_id: Mapping[str, RealityGapEvidenceReference],
    ) -> None:
        trace = value.decision_trace
        known = set(evidence_by_id)
        if not set(trace.evidence_considered) <= known:
            raise ValueError("Decision Trace considered evidence reference does not resolve")
        if not set(trace.evidence_rejected) <= known:
            raise ValueError("Decision Trace rejected evidence reference does not resolve")
        if set(trace.evidence_considered) & set(trace.evidence_rejected):
            raise ValueError("Decision Trace evidence groups must be disjoint")
        if any(evidence_by_id[item].eligibility == RealityGapEvidenceEligibility.INELIGIBLE for item in trace.evidence_considered):
            raise ValueError("INELIGIBLE evidence must not be considered")
        if trace.severity_output is not None and value.severity is not None and trace.severity_output != value.severity:
            raise ValueError("Decision Trace severity does not match supplied severity")
        metric_values = {
            "surprise_score": value.surprise_score,
            "surprise": value.surprise_score,
            "knowledge_gap_score": value.knowledge_gap_score,
            "knowledge_gap": value.knowledge_gap_score,
            "explanation_confidence": value.explanation_confidence,
            "unexplained_residual_score": value.unexplained_residual_score,
            "unexplained_residual": value.unexplained_residual_score,
        }
        for key, expected in metric_values.items():
            if key in trace.metric_outputs and trace.metric_outputs[key] != expected:
                raise ValueError("Decision Trace metric output mismatch: {0}".format(key))
        policy_values = {
            "analysis_policy_version": value.analysis_policy_version,
            "classification_policy_version": value.provenance.classification_policy_version,
            "classification": value.provenance.classification_policy_version,
            "candidate_policy_version": value.provenance.candidate_policy_version,
            "candidate": value.provenance.candidate_policy_version,
            "metric_version": value.metric_version,
            "metric_policy_version": value.provenance.metric_policy_version,
            "metric": value.provenance.metric_policy_version,
            "severity_policy_version": value.provenance.severity_policy_version,
            "severity": value.provenance.severity_policy_version,
            "tree_version": value.tree_version,
            "tree_policy_version": value.provenance.tree_policy_version,
            "tree": value.provenance.tree_policy_version,
            "trace_version": value.trace_version,
            "trace_policy_version": value.provenance.trace_policy_version,
            "trace": value.provenance.trace_policy_version,
            "taxonomy_version": value.taxonomy_version,
            "taxonomy": value.provenance.taxonomy_version,
        }
        for key, expected in policy_values.items():
            if key in trace.policy_versions and trace.policy_versions[key] != expected:
                raise ValueError("Decision Trace policy version mismatch: {0}".format(key))

    @staticmethod
    def _validate_capabilities(value: RealityGapAssemblyInput) -> None:
        capabilities = value.analysis_capabilities
        dimensions = set(value.dimensions)
        if not capabilities.supports_root_cause_candidates and value.root_cause_candidates:
            raise ValueError("root-cause candidates are unsupported by declared capabilities")
        if not capabilities.supports_root_cause_tree and value.root_cause_tree is not None:
            raise ValueError("root-cause tree is unsupported by declared capabilities")
        if not capabilities.supports_market_gap and RealityGapDimension.MARKET in dimensions:
            raise ValueError("MARKET dimension is unsupported by declared capabilities")
        specific_intelligence_types = set(value.intelligence_gap_types) - {IntelligenceGapType.UNKNOWN}
        if not capabilities.supports_intelligence_gap and (specific_intelligence_types or RealityGapDimension.INTELLIGENCE in dimensions):
            raise ValueError("Intelligence Gap is unsupported by declared capabilities")
        if not capabilities.supports_observability_gap and (
            value.observability_gap_types or value.observability_gaps or RealityGapDimension.OBSERVABILITY in dimensions
        ):
            raise ValueError("Observability Gap is unsupported by declared capabilities")
        if not capabilities.supports_explanation_gap and (
            value.explanation_gap is not None or RealityGapDimension.EXPLANATION in dimensions
        ):
            raise ValueError("Explanation Gap is unsupported by declared capabilities")

    @staticmethod
    def _validate_optional_outputs(value: RealityGapAssemblyInput) -> None:
        capabilities = value.analysis_capabilities
        trace_outputs = value.decision_trace.metric_outputs
        if not capabilities.supports_knowledge_gap_metric and value.knowledge_gap_score is not None:
            raise ValueError("unsupported knowledge gap metric must be None")
        if not capabilities.supports_knowledge_gap_metric and any(
            trace_outputs.get(key) is not None for key in ("knowledge_gap_score", "knowledge_gap")
        ):
            raise ValueError("unsupported knowledge gap metric must be absent from Decision Trace")
        if not capabilities.supports_explanation_confidence_metric and value.explanation_confidence is not None:
            raise ValueError("unsupported explanation confidence must be None")
        if not capabilities.supports_explanation_confidence_metric and trace_outputs.get("explanation_confidence") is not None:
            raise ValueError("unsupported explanation confidence must be absent from Decision Trace")
        if not capabilities.supports_severity and value.severity is not None:
            raise ValueError("unsupported severity must be None")
        if not capabilities.supports_severity and value.decision_trace.severity_output is not None:
            raise ValueError("unsupported severity must be absent from Decision Trace")
        if (value.knowledge_gap_score is not None or value.explanation_confidence is not None) and value.metric_version is None:
            raise ValueError("metric_version is required for populated optional metrics")
        if value.root_cause_tree is not None and value.tree_version is None:
            raise ValueError("tree_version is required when a tree exists")
        if value.severity is not None and value.provenance.severity_policy_version is None:
            raise ValueError("severity policy version is required when severity exists")

    @staticmethod
    def _warnings(
        value: RealityGapAssemblyInput,
        evidence: Tuple[RealityGapEvidenceReference, ...],
        eligible_ids: Tuple[str, ...],
        ineligible_ids: Tuple[str, ...],
        candidates: Tuple[RootCauseCandidate, ...],
    ) -> Tuple[str, ...]:
        warnings = []
        if not eligible_ids:
            warnings.append("no eligible evidence supplied")
        if value.analysis_capabilities.supports_root_cause_candidates and not candidates:
            warnings.append("no Root Cause Candidate supplied despite supported capability")
        if not value.analysis_capabilities.supports_knowledge_gap_metric:
            warnings.append("knowledge gap metric intentionally unavailable")
        if not value.analysis_capabilities.supports_explanation_confidence_metric:
            warnings.append("explanation confidence metric intentionally unavailable")
        if value.analysis_capabilities.supports_root_cause_tree and value.root_cause_tree is None:
            warnings.append("tree capability supported but tree omitted")
        if evidence and all(item.evidence_type == RealityGapEvidenceType.OBSERVABILITY_FACT for item in evidence):
            warnings.append("only observability evidence is available")
        if value.analysis_capabilities.supports_explanation_gap and value.explanation_gap is None:
            warnings.append("optional explanation gap omitted")
        if ineligible_ids:
            warnings.append("analysis contains ineligible audit evidence")
            if not set(ineligible_ids) <= set(value.decision_trace.evidence_rejected):
                warnings.append("ineligible audit evidence is not listed as rejected in Decision Trace")
        return _ordered_warnings(tuple(warnings))


__all__ = ["RealityGapAssembler", "RealityGapAssemblyInput", "RealityGapAssemblyResult"]
