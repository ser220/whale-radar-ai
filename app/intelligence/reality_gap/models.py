"""Immutable, serialization-safe Reality Gap domain contracts."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional, Tuple

from .enums import (
    IntelligenceGapType,
    ObservabilityGapType,
    RealityGapDimension,
    RealityGapEvidenceEligibility,
    RealityGapEvidenceRelation,
    RealityGapEvidenceType,
    RealityGapPrimaryType,
    RealityGapSeverity,
    RootCauseCategory,
    RootCauseDisposition,
    RootCauseRole,
)
from .tree import RootCauseTree, validate_root_cause_tree
from .validation import (
    enum_tuple,
    enum_value,
    frozen_mapping,
    mapping_payload,
    nonnegative_integer,
    optional_nonnegative_integer,
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


def _bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError("{0} must be a boolean".format(field_name))
    return value


@dataclass(frozen=True)
class AnalysisProvenance:
    analysis_engine_version: str
    classification_policy_version: str
    candidate_policy_version: str
    metric_policy_version: Optional[str]
    severity_policy_version: Optional[str]
    tree_policy_version: str
    trace_policy_version: str
    taxonomy_version: str
    serialization_version: str
    created_by: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "analysis_engine_version", "classification_policy_version",
            "candidate_policy_version", "tree_policy_version", "trace_policy_version",
            "taxonomy_version", "serialization_version", "created_by",
        ):
            object.__setattr__(self, name, required_text(getattr(self, name), name))
        object.__setattr__(self, "metric_policy_version", optional_text(self.metric_policy_version, "metric_policy_version"))
        object.__setattr__(self, "severity_policy_version", optional_text(self.severity_policy_version, "severity_policy_version"))
        object.__setattr__(self, "metadata", frozen_mapping(self.metadata))

    def to_dict(self) -> dict:
        return plain(self.__dict__)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AnalysisProvenance":
        return cls(**mapping_payload(value, cls.__name__))


@dataclass(frozen=True)
class AnalysisCapabilities:
    supports_market_gap: bool
    supports_intelligence_gap: bool
    supports_observability_gap: bool
    supports_explanation_gap: bool
    supports_root_cause_candidates: bool
    supports_root_cause_tree: bool
    supports_knowledge_gap_metric: bool
    supports_explanation_confidence_metric: bool
    supports_severity: bool
    supports_decision_trace: bool
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "supports_market_gap", "supports_intelligence_gap", "supports_observability_gap",
            "supports_explanation_gap", "supports_root_cause_candidates", "supports_root_cause_tree",
            "supports_knowledge_gap_metric", "supports_explanation_confidence_metric",
            "supports_severity", "supports_decision_trace",
        ):
            object.__setattr__(self, name, _bool(getattr(self, name), name))
        object.__setattr__(self, "metadata", frozen_mapping(self.metadata))

    def to_dict(self) -> dict:
        return plain(self.__dict__)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AnalysisCapabilities":
        return cls(**mapping_payload(value, cls.__name__))


@dataclass(frozen=True)
class RealityGapEvidenceReference:
    evidence_id: str
    evidence_type: RealityGapEvidenceType
    relation: RealityGapEvidenceRelation
    eligibility: RealityGapEvidenceEligibility
    artifact_id: str
    timeline_id: str
    timeline_version: int
    entry_id: Optional[str]
    observed_at: datetime
    factor_name: Optional[str]
    measured_value: Optional[float]
    availability: Optional[str]
    delta_state: Optional[str]
    prior_value: Optional[float]
    new_value: Optional[float]
    criterion_reference: Optional[str]
    rejection_reason: Optional[str]
    quality: Optional[float]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("evidence_id", "artifact_id", "timeline_id"):
            object.__setattr__(self, name, required_text(getattr(self, name), name))
        object.__setattr__(self, "evidence_type", enum_value(self.evidence_type, RealityGapEvidenceType, "evidence_type"))
        object.__setattr__(self, "relation", enum_value(self.relation, RealityGapEvidenceRelation, "relation"))
        eligibility = enum_value(self.eligibility, RealityGapEvidenceEligibility, "eligibility")
        object.__setattr__(self, "eligibility", eligibility)
        object.__setattr__(self, "timeline_version", positive_integer(self.timeline_version, "timeline_version"))
        object.__setattr__(self, "entry_id", optional_text(self.entry_id, "entry_id"))
        object.__setattr__(self, "observed_at", utc_datetime(self.observed_at, "observed_at"))
        for name in ("factor_name", "availability", "delta_state", "criterion_reference", "rejection_reason"):
            object.__setattr__(self, name, optional_text(getattr(self, name), name))
        for name in ("measured_value", "prior_value", "new_value", "quality"):
            object.__setattr__(self, name, optional_percentage(getattr(self, name), name))
        if eligibility == RealityGapEvidenceEligibility.INELIGIBLE and self.rejection_reason is None:
            raise ValueError("INELIGIBLE evidence requires rejection_reason")
        if eligibility == RealityGapEvidenceEligibility.ELIGIBLE and self.rejection_reason is not None:
            raise ValueError("ELIGIBLE evidence must not carry rejection_reason")
        if self.availability is not None and self.availability.upper() != "AVAILABLE" and self.measured_value is not None:
            raise ValueError("unavailable evidence must not carry measured_value")
        object.__setattr__(self, "metadata", frozen_mapping(self.metadata))

    def to_dict(self) -> dict:
        return plain(self.__dict__)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RealityGapEvidenceReference":
        data = mapping_payload(value, cls.__name__)
        data["observed_at"] = parse_datetime(data["observed_at"], "observed_at")
        return cls(**data)


@dataclass(frozen=True)
class ObservabilityGapRecord:
    gap_type: ObservabilityGapType
    subject: str
    availability: Optional[str]
    expected_count: Optional[int]
    measured_count: Optional[int]
    coverage_ratio: Optional[float]
    quality: Optional[float]
    affected_criteria: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]
    reason: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "gap_type", enum_value(self.gap_type, ObservabilityGapType, "gap_type"))
        object.__setattr__(self, "subject", required_text(self.subject, "subject"))
        object.__setattr__(self, "availability", optional_text(self.availability, "availability"))
        object.__setattr__(self, "expected_count", optional_nonnegative_integer(self.expected_count, "expected_count"))
        object.__setattr__(self, "measured_count", optional_nonnegative_integer(self.measured_count, "measured_count"))
        if self.expected_count is not None and self.measured_count is not None and self.measured_count > self.expected_count:
            raise ValueError("measured_count must not exceed expected_count")
        object.__setattr__(self, "coverage_ratio", optional_percentage(self.coverage_ratio, "coverage_ratio"))
        object.__setattr__(self, "quality", optional_percentage(self.quality, "quality"))
        object.__setattr__(self, "affected_criteria", text_tuple(self.affected_criteria, "affected_criteria"))
        object.__setattr__(self, "evidence_refs", text_tuple(self.evidence_refs, "evidence_refs"))
        object.__setattr__(self, "reason", required_text(self.reason, "reason"))
        object.__setattr__(self, "metadata", frozen_mapping(self.metadata))

    def to_dict(self) -> dict:
        return plain(self.__dict__)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ObservabilityGapRecord":
        return cls(**mapping_payload(value, cls.__name__))


@dataclass(frozen=True)
class ExplanationGapRecord:
    unexplained_residual_score: Optional[float]
    conflicting_candidate_count: int
    eligible_evidence_count: int
    accepted_candidate_count: int
    uncovered_criteria: Tuple[str, ...]
    limitations: Tuple[str, ...]
    reason: str
    policy_version: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "unexplained_residual_score", optional_percentage(self.unexplained_residual_score, "unexplained_residual_score"))
        for name in ("conflicting_candidate_count", "eligible_evidence_count", "accepted_candidate_count"):
            object.__setattr__(self, name, nonnegative_integer(getattr(self, name), name))
        object.__setattr__(self, "uncovered_criteria", text_tuple(self.uncovered_criteria, "uncovered_criteria"))
        object.__setattr__(self, "limitations", text_tuple(self.limitations, "limitations"))
        object.__setattr__(self, "reason", required_text(self.reason, "reason"))
        object.__setattr__(self, "policy_version", required_text(self.policy_version, "policy_version"))
        object.__setattr__(self, "metadata", frozen_mapping(self.metadata))

    def to_dict(self) -> dict:
        return plain(self.__dict__)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExplanationGapRecord":
        return cls(**mapping_payload(value, cls.__name__))


@dataclass(frozen=True)
class RootCauseCandidate:
    candidate_id: str
    category: RootCauseCategory
    subject: str
    description: str
    role: RootCauseRole
    disposition: RootCauseDisposition
    confidence: Optional[float]
    temporal_precedence: Optional[float]
    direct_relevance: Optional[float]
    evidence_coverage: Optional[float]
    independent_support_count: int
    supporting_evidence_refs: Tuple[str, ...]
    contradicting_evidence_refs: Tuple[str, ...]
    parent_candidate_id: Optional[str]
    child_candidate_ids: Tuple[str, ...]
    limitations: Tuple[str, ...]
    alternative_candidate_ids: Tuple[str, ...]
    rejection_reason: Optional[str]
    policy_version: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        candidate_id = required_text(self.candidate_id, "candidate_id")
        object.__setattr__(self, "candidate_id", candidate_id)
        object.__setattr__(self, "category", enum_value(self.category, RootCauseCategory, "category"))
        object.__setattr__(self, "subject", required_text(self.subject, "subject"))
        object.__setattr__(self, "description", required_text(self.description, "description"))
        role = enum_value(self.role, RootCauseRole, "role")
        disposition = enum_value(self.disposition, RootCauseDisposition, "disposition")
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "disposition", disposition)
        for name in ("confidence", "temporal_precedence", "direct_relevance", "evidence_coverage"):
            object.__setattr__(self, name, optional_percentage(getattr(self, name), name))
        object.__setattr__(self, "independent_support_count", nonnegative_integer(self.independent_support_count, "independent_support_count"))
        supporting = text_tuple(self.supporting_evidence_refs, "supporting_evidence_refs")
        contradicting = text_tuple(self.contradicting_evidence_refs, "contradicting_evidence_refs")
        if set(supporting) & set(contradicting):
            raise ValueError("supporting and contradicting evidence must be disjoint")
        object.__setattr__(self, "supporting_evidence_refs", supporting)
        object.__setattr__(self, "contradicting_evidence_refs", contradicting)
        parent = optional_text(self.parent_candidate_id, "parent_candidate_id")
        children = text_tuple(self.child_candidate_ids, "child_candidate_ids")
        alternatives = text_tuple(self.alternative_candidate_ids, "alternative_candidate_ids")
        if parent == candidate_id or candidate_id in children or candidate_id in alternatives:
            raise ValueError("candidate must not reference itself")
        object.__setattr__(self, "parent_candidate_id", parent)
        object.__setattr__(self, "child_candidate_ids", children)
        object.__setattr__(self, "limitations", text_tuple(self.limitations, "limitations"))
        object.__setattr__(self, "alternative_candidate_ids", alternatives)
        rejection_reason = optional_text(self.rejection_reason, "rejection_reason")
        if disposition == RootCauseDisposition.REJECTED:
            if rejection_reason is None:
                raise ValueError("REJECTED candidate requires rejection_reason")
            if role != RootCauseRole.REJECTED_CANDIDATE:
                raise ValueError("REJECTED candidate must have REJECTED_CANDIDATE role")
        elif rejection_reason is not None:
            raise ValueError("non-rejected candidate must not carry rejection_reason")
        elif role == RootCauseRole.REJECTED_CANDIDATE:
            raise ValueError("REJECTED_CANDIDATE role requires REJECTED disposition")
        object.__setattr__(self, "rejection_reason", rejection_reason)
        object.__setattr__(self, "policy_version", required_text(self.policy_version, "policy_version"))
        object.__setattr__(self, "metadata", frozen_mapping(self.metadata))

    def to_dict(self) -> dict:
        return plain(self.__dict__)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RootCauseCandidate":
        return cls(**mapping_payload(value, cls.__name__))


@dataclass(frozen=True)
class RealityGapDecisionTrace:
    trace_id: str
    trace_version: str
    expectation_status: str
    evaluation_gap_type: str
    eligible_window_start: datetime
    eligible_window_end: datetime
    evidence_considered: Tuple[str, ...]
    evidence_rejected: Tuple[str, ...]
    gap_dimensions_considered: Tuple[RealityGapDimension, ...]
    classification_steps: Tuple[str, ...]
    candidate_generation_steps: Tuple[str, ...]
    candidate_acceptance_steps: Tuple[str, ...]
    candidate_rejection_steps: Tuple[str, ...]
    metric_inputs: Mapping[str, Any]
    metric_outputs: Mapping[str, Any]
    severity_inputs: Mapping[str, Any]
    severity_output: Optional[RealityGapSeverity]
    unresolved_questions: Tuple[str, ...]
    policy_versions: Mapping[str, Any]
    created_at: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("trace_id", "trace_version", "expectation_status", "evaluation_gap_type"):
            object.__setattr__(self, name, required_text(getattr(self, name), name))
        start = utc_datetime(self.eligible_window_start, "eligible_window_start")
        end = utc_datetime(self.eligible_window_end, "eligible_window_end")
        if start > end:
            raise ValueError("eligible_window_start must not be after eligible_window_end")
        object.__setattr__(self, "eligible_window_start", start)
        object.__setattr__(self, "eligible_window_end", end)
        for name in (
            "evidence_considered", "evidence_rejected", "classification_steps",
            "candidate_generation_steps", "candidate_acceptance_steps",
            "candidate_rejection_steps", "unresolved_questions",
        ):
            object.__setattr__(self, name, text_tuple(getattr(self, name), name))
        if set(self.evidence_considered) & set(self.evidence_rejected):
            raise ValueError("considered and rejected evidence must be disjoint")
        object.__setattr__(self, "gap_dimensions_considered", enum_tuple(self.gap_dimensions_considered, RealityGapDimension, "gap_dimensions_considered"))
        for name in ("metric_inputs", "metric_outputs", "severity_inputs", "policy_versions", "metadata"):
            object.__setattr__(self, name, frozen_mapping(getattr(self, name), name))
        if self.severity_output is not None:
            object.__setattr__(self, "severity_output", enum_value(self.severity_output, RealityGapSeverity, "severity_output"))
        object.__setattr__(self, "created_at", utc_datetime(self.created_at, "created_at"))

    def to_dict(self) -> dict:
        return plain(self.__dict__)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RealityGapDecisionTrace":
        data = mapping_payload(value, cls.__name__)
        for name in ("eligible_window_start", "eligible_window_end", "created_at"):
            data[name] = parse_datetime(data[name], name)
        return cls(**data)


@dataclass(frozen=True)
class RealityGapAnalysis:
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
    root_cause_candidates: Tuple[RootCauseCandidate, ...]
    root_cause_tree: Optional[RootCauseTree]
    accepted_candidate_ids: Tuple[str, ...]
    rejected_candidate_ids: Tuple[str, ...]
    unresolved_candidate_ids: Tuple[str, ...]
    supporting_evidence: Tuple[RealityGapEvidenceReference, ...]
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
        candidates = typed_tuple(self.root_cause_candidates, RootCauseCandidate, "root_cause_candidates")
        candidate_ids = tuple(candidate.candidate_id for candidate in candidates)
        if len(set(candidate_ids)) != len(candidate_ids):
            raise ValueError("duplicate candidate IDs are forbidden")
        object.__setattr__(self, "root_cause_candidates", candidates)
        accepted = text_tuple(self.accepted_candidate_ids, "accepted_candidate_ids")
        rejected = text_tuple(self.rejected_candidate_ids, "rejected_candidate_ids")
        unresolved = text_tuple(self.unresolved_candidate_ids, "unresolved_candidate_ids")
        grouped = accepted + rejected + unresolved
        if len(set(grouped)) != len(grouped):
            raise ValueError("candidate disposition groups must be disjoint")
        if set(grouped) != set(candidate_ids):
            raise ValueError("candidate disposition groups must resolve and cover candidates")
        by_id = {candidate.candidate_id: candidate for candidate in candidates}
        expected_accepted = {cid for cid, candidate in by_id.items() if candidate.disposition in (RootCauseDisposition.ACCEPTED, RootCauseDisposition.PARTIALLY_SUPPORTED)}
        expected_rejected = {cid for cid, candidate in by_id.items() if candidate.disposition == RootCauseDisposition.REJECTED}
        expected_unresolved = {cid for cid, candidate in by_id.items() if candidate.disposition == RootCauseDisposition.UNRESOLVED}
        if set(accepted) != expected_accepted or set(rejected) != expected_rejected or set(unresolved) != expected_unresolved:
            raise ValueError("analysis groups must match candidate dispositions")
        object.__setattr__(self, "accepted_candidate_ids", accepted)
        object.__setattr__(self, "rejected_candidate_ids", rejected)
        object.__setattr__(self, "unresolved_candidate_ids", unresolved)
        evidence = typed_tuple(self.supporting_evidence, RealityGapEvidenceReference, "supporting_evidence")
        evidence_ids = tuple(item.evidence_id for item in evidence)
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("duplicate evidence IDs are forbidden")
        known_evidence = set(evidence_ids)
        for candidate in candidates:
            if not set(candidate.supporting_evidence_refs + candidate.contradicting_evidence_refs) <= known_evidence:
                raise ValueError("candidate evidence reference does not resolve")
        object.__setattr__(self, "supporting_evidence", evidence)
        gaps = typed_tuple(self.observability_gaps, ObservabilityGapRecord, "observability_gaps")
        if any(not set(gap.evidence_refs) <= known_evidence for gap in gaps):
            raise ValueError("observability evidence reference does not resolve")
        object.__setattr__(self, "observability_gaps", gaps)
        if self.explanation_gap is not None and not isinstance(self.explanation_gap, ExplanationGapRecord):
            raise TypeError("explanation_gap must be an ExplanationGapRecord")
        if self.root_cause_tree is not None:
            if not isinstance(self.root_cause_tree, RootCauseTree):
                raise TypeError("root_cause_tree must be a RootCauseTree")
            validate_root_cause_tree(self.root_cause_tree, candidates)
        object.__setattr__(self, "source_expectation_snapshot", frozen_mapping(self.source_expectation_snapshot, "source_expectation_snapshot"))
        object.__setattr__(self, "source_evaluation_snapshot", frozen_mapping(self.source_evaluation_snapshot, "source_evaluation_snapshot"))
        timeline_versions = positive_integer_tuple(self.source_timeline_versions, "source_timeline_versions", required=True)
        entry_ids = text_tuple(self.source_entry_ids, "source_entry_ids", required=True)
        object.__setattr__(self, "source_timeline_versions", timeline_versions)
        object.__setattr__(self, "source_entry_ids", entry_ids)
        for name in ("analysis_policy_version", "taxonomy_version", "trace_version"):
            object.__setattr__(self, name, required_text(getattr(self, name), name))
        for name in ("metric_version", "tree_version"):
            object.__setattr__(self, name, optional_text(getattr(self, name), name))
        if not isinstance(self.provenance, AnalysisProvenance):
            raise TypeError("provenance must be AnalysisProvenance")
        if not isinstance(self.analysis_capabilities, AnalysisCapabilities):
            raise TypeError("analysis_capabilities must be AnalysisCapabilities")
        if not isinstance(self.decision_trace, RealityGapDecisionTrace):
            raise TypeError("decision_trace must be RealityGapDecisionTrace")
        if not set(self.decision_trace.evidence_considered + self.decision_trace.evidence_rejected) <= known_evidence:
            raise ValueError("decision trace evidence reference does not resolve")
        evidence_by_id = {item.evidence_id: item for item in evidence}
        for evidence_id in self.decision_trace.evidence_considered:
            item = evidence_by_id[evidence_id]
            if item.eligibility != RealityGapEvidenceEligibility.ELIGIBLE:
                raise ValueError("considered evidence must be ELIGIBLE")
            if not self.decision_trace.eligible_window_start <= item.observed_at <= self.decision_trace.eligible_window_end:
                raise ValueError("considered evidence must be inside the eligible window")
        if self.trace_version != self.decision_trace.trace_version or self.trace_version != self.provenance.trace_policy_version:
            raise ValueError("trace versions must agree")
        if self.analysis_policy_version != self.provenance.classification_policy_version:
            raise ValueError("analysis policy versions must agree")
        if self.metric_version != self.provenance.metric_policy_version:
            raise ValueError("metric versions must agree")
        if self.taxonomy_version != self.provenance.taxonomy_version:
            raise ValueError("taxonomy versions must agree")
        if self.root_cause_tree is None:
            if self.tree_version is not None:
                raise ValueError("tree_version requires root_cause_tree")
        elif self.tree_version != self.root_cause_tree.tree_version or self.tree_version != self.provenance.tree_policy_version:
            raise ValueError("tree versions must agree")
        capabilities = self.analysis_capabilities
        if not capabilities.supports_knowledge_gap_metric and self.knowledge_gap_score is not None:
            raise ValueError("unsupported knowledge gap metric must be None")
        if not capabilities.supports_explanation_confidence_metric and self.explanation_confidence is not None:
            raise ValueError("unsupported explanation confidence must be None")
        if not capabilities.supports_root_cause_tree and self.root_cause_tree is not None:
            raise ValueError("unsupported root-cause tree must be None")
        if not capabilities.supports_severity and self.severity is not None:
            raise ValueError("unsupported severity must be None")
        revision_reason = optional_text(self.revision_reason, "revision_reason")
        if version > 1 and revision_reason is None:
            raise ValueError("analysis version greater than 1 requires revision_reason")
        object.__setattr__(self, "revision_reason", revision_reason)
        object.__setattr__(self, "metadata", frozen_mapping(self.metadata))

    def to_dict(self) -> dict:
        payload = plain(self.__dict__)
        payload["root_cause_candidates"] = [item.to_dict() for item in self.root_cause_candidates]
        payload["root_cause_tree"] = None if self.root_cause_tree is None else self.root_cause_tree.to_dict()
        payload["supporting_evidence"] = [item.to_dict() for item in self.supporting_evidence]
        payload["observability_gaps"] = [item.to_dict() for item in self.observability_gaps]
        payload["explanation_gap"] = None if self.explanation_gap is None else self.explanation_gap.to_dict()
        payload["provenance"] = self.provenance.to_dict()
        payload["analysis_capabilities"] = self.analysis_capabilities.to_dict()
        payload["decision_trace"] = self.decision_trace.to_dict()
        return payload

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RealityGapAnalysis":
        data = mapping_payload(value, cls.__name__)
        for name in ("created_at", "evaluated_at"):
            data[name] = parse_datetime(data[name], name)
        data["root_cause_candidates"] = tuple(RootCauseCandidate.from_dict(item) for item in data["root_cause_candidates"])
        data["root_cause_tree"] = None if data["root_cause_tree"] is None else RootCauseTree.from_dict(data["root_cause_tree"])
        data["supporting_evidence"] = tuple(RealityGapEvidenceReference.from_dict(item) for item in data["supporting_evidence"])
        data["observability_gaps"] = tuple(ObservabilityGapRecord.from_dict(item) for item in data["observability_gaps"])
        data["explanation_gap"] = None if data["explanation_gap"] is None else ExplanationGapRecord.from_dict(data["explanation_gap"])
        data["provenance"] = AnalysisProvenance.from_dict(data["provenance"])
        data["analysis_capabilities"] = AnalysisCapabilities.from_dict(data["analysis_capabilities"])
        data["decision_trace"] = RealityGapDecisionTrace.from_dict(data["decision_trace"])
        return cls(**data)


def validate_analysis_revision(previous: RealityGapAnalysis, current: RealityGapAnalysis) -> None:
    """Validate immutable lineage and prevent expansion beyond evaluated evidence."""

    if not isinstance(previous, RealityGapAnalysis) or not isinstance(current, RealityGapAnalysis):
        raise TypeError("previous and current must be RealityGapAnalysis")
    for name in ("gap_id", "expectation_id", "evaluation_id", "timeline_id", "asset"):
        if getattr(previous, name) != getattr(current, name):
            raise ValueError("analysis revision identity mismatch: {0}".format(name))
    if current.analysis_version != previous.analysis_version + 1:
        raise ValueError("analysis revision version must increment by one")
    if current.revision_reason is None:
        raise ValueError("analysis revision requires revision_reason")
    if current.evaluated_at != previous.evaluated_at:
        raise ValueError("analysis revision must preserve evaluated_at boundary")
    if current.decision_trace.eligible_window_start != previous.decision_trace.eligible_window_start or current.decision_trace.eligible_window_end != previous.decision_trace.eligible_window_end:
        raise ValueError("analysis revision must preserve eligible evidence window")
    if not set(current.source_timeline_versions) <= set(previous.source_timeline_versions):
        raise ValueError("analysis revision introduces later Timeline versions")
    if not set(current.source_entry_ids) <= set(previous.source_entry_ids):
        raise ValueError("analysis revision introduces out-of-bound entries")
    previous_evidence_ids = {item.evidence_id for item in previous.supporting_evidence}
    current_evidence_ids = {item.evidence_id for item in current.supporting_evidence}
    if not current_evidence_ids <= previous_evidence_ids:
        raise ValueError("analysis revision introduces new evidence")


__all__ = [
    "AnalysisCapabilities", "AnalysisProvenance", "ExplanationGapRecord",
    "ObservabilityGapRecord", "RealityGapAnalysis", "RealityGapDecisionTrace",
    "RealityGapEvidenceReference", "RootCauseCandidate", "validate_analysis_revision",
]
