"""Pure deterministic materialization of approved projection mapping inputs."""

from typing import Dict, Union

from app.intelligence.reality_gap.enums import (
    RealityGapEvidenceEligibility,
    RootCauseDisposition,
    RootCauseRole,
)
from app.intelligence.reality_gap.models import RootCauseCandidate

from .mapping_models import (
    MappingFailureCategory,
    RootCauseCandidateMappingFailure,
    RootCauseCandidateMappingRequest,
    RootCauseCandidateMappingResult,
)


MappingOutcome = Union[
    RootCauseCandidateMappingResult,
    RootCauseCandidateMappingFailure,
]


def _failure(
    request: RootCauseCandidateMappingRequest,
    category: MappingFailureCategory,
    reason: str,
) -> RootCauseCandidateMappingFailure:
    projection = request.source_projection
    return RootCauseCandidateMappingFailure(
        category=category,
        reason=reason,
        source_projection_id=None if projection is None else projection.projection_id,
        source_projection_version=None if projection is None else projection.projection_version,
        mapping_policy_version=request.mapping_policy_version,
        created_at=request.created_at,
        metadata={"partial_candidate_created": False},
    )


def map_projection_to_root_cause_candidate(
    request: RootCauseCandidateMappingRequest,
) -> MappingOutcome:
    """Map immutable explicit inputs without inference, I/O, clock, or mutation."""

    if not isinstance(request, RootCauseCandidateMappingRequest):
        raise TypeError("request must be a RootCauseCandidateMappingRequest")
    projection = request.source_projection
    if projection is None:
        return _failure(request, MappingFailureCategory.UNKNOWN_PROJECTION, "source projection is required")
    descriptor = request.explanation_descriptor
    if descriptor is None:
        return _failure(request, MappingFailureCategory.LINEAGE_MISMATCH, "explanation descriptor is required")
    decision = request.explanation_decision_snapshot
    if decision is None:
        return _failure(request, MappingFailureCategory.MISSING_DECISION_SNAPSHOT, "explanation decision snapshot is required")
    placement = request.placement_snapshot
    if placement is None:
        return _failure(request, MappingFailureCategory.INVALID_PLACEMENT_CONTEXT, "placement snapshot is required")
    catalog = request.evidence_catalog_view
    if catalog is None:
        return _failure(request, MappingFailureCategory.INVALID_EVIDENCE_REFERENCE, "evidence catalog view is required")

    if request.created_at < projection.created_at:
        return _failure(request, MappingFailureCategory.LINEAGE_MISMATCH, "mapping predates the source projection")
    if descriptor.created_at > request.created_at or decision.created_at > request.created_at or placement.created_at > request.created_at or catalog.created_at > request.created_at:
        return _failure(request, MappingFailureCategory.LINEAGE_MISMATCH, "mapping input is newer than the mapping boundary")
    if descriptor.candidate_id != projection.candidate_id or descriptor.candidate_version != projection.candidate_version:
        return _failure(request, MappingFailureCategory.LINEAGE_MISMATCH, "descriptor candidate lineage does not match projection")
    if decision.projection_id != projection.projection_id or decision.projection_version != projection.projection_version:
        return _failure(request, MappingFailureCategory.LINEAGE_MISMATCH, "decision projection lineage does not match projection")
    if decision.mapping_policy_version != request.mapping_policy_version:
        return _failure(request, MappingFailureCategory.POLICY_CONFLICT, "decision mapping policy does not match request")
    if decision.role != projection.role or decision.disposition != projection.disposition:
        return _failure(request, MappingFailureCategory.MISSING_DECISION_SNAPSHOT, "explicit role/disposition does not match projection")

    if decision.disposition == RootCauseDisposition.REJECTED:
        if decision.role != RootCauseRole.REJECTED_CANDIDATE or decision.rejection_reason is None:
            return _failure(request, MappingFailureCategory.MISSING_DECISION_SNAPSHOT, "rejected decision requires rejected role and reason")
    elif decision.role == RootCauseRole.REJECTED_CANDIDATE or decision.rejection_reason is not None:
        return _failure(request, MappingFailureCategory.MISSING_DECISION_SNAPSHOT, "non-rejected decision cannot carry rejected role or reason")

    if placement.target_projection_id != projection.projection_id or placement.tree_context_reference != projection.tree_context_reference:
        return _failure(request, MappingFailureCategory.INVALID_PLACEMENT_CONTEXT, "placement context does not match projection")

    evidence_by_id: Dict[str, object] = {item.evidence_id: item for item in catalog.entries}
    snapshot = projection.evidence_reference_snapshot
    evidence_refs = snapshot.supporting_evidence_refs + snapshot.contradicting_evidence_refs
    if set(evidence_by_id) != set(evidence_refs):
        return _failure(request, MappingFailureCategory.INVALID_EVIDENCE_REFERENCE, "evidence catalog must be scoped exactly to projection references")
    if any(reference not in evidence_by_id for reference in evidence_refs):
        return _failure(request, MappingFailureCategory.INVALID_EVIDENCE_REFERENCE, "projection evidence reference does not resolve")
    if any(evidence_by_id[reference].observed_at > projection.created_at for reference in evidence_refs):
        return _failure(request, MappingFailureCategory.INVALID_EVIDENCE_REFERENCE, "future evidence is outside the projection boundary")
    if any(evidence_by_id[reference].eligibility != RealityGapEvidenceEligibility.ELIGIBLE for reference in snapshot.supporting_evidence_refs):
        return _failure(request, MappingFailureCategory.INVALID_EVIDENCE_REFERENCE, "supporting evidence must preserve eligible status")
    if decision.independent_support_count > len(snapshot.supporting_evidence_refs):
        return _failure(request, MappingFailureCategory.MISSING_DECISION_SNAPSHOT, "independent support count exceeds supporting references")

    lineage_metadata = {
        "source_candidate_id": projection.candidate_id,
        "source_candidate_version": projection.candidate_version,
        "source_projection_id": projection.projection_id,
        "source_projection_version": projection.projection_version,
        "projection_policy_version": projection.projection_policy_version,
        "mapping_policy_version": request.mapping_policy_version,
        "analysis_context_id": projection.analysis_context_id,
        "tree_context_reference": placement.tree_context_reference,
        "tree_version": placement.tree_version,
        "hypothesis_reference": descriptor.hypothesis_reference,
        "descriptor_policy_version": descriptor.descriptor_policy_version,
        "decision_reference": decision.decision_reference,
        "decision_policy_version": decision.decision_policy_version,
        "independent_support_provenance_reference": decision.independent_support_provenance_reference,
        "placement_policy_version": placement.placement_policy_version,
        "evidence_catalog_id": catalog.catalog_id,
        "evidence_catalog_version": catalog.catalog_version,
    }
    candidate = RootCauseCandidate(
        candidate_id=projection.projection_id,
        category=projection.category,
        subject=descriptor.subject,
        description=descriptor.description,
        role=decision.role,
        disposition=decision.disposition,
        confidence=None,
        temporal_precedence=None,
        direct_relevance=None,
        evidence_coverage=None,
        independent_support_count=decision.independent_support_count,
        supporting_evidence_refs=snapshot.supporting_evidence_refs,
        contradicting_evidence_refs=snapshot.contradicting_evidence_refs,
        parent_candidate_id=placement.parent_projection_id,
        child_candidate_ids=placement.child_projection_ids,
        limitations=snapshot.limitation_references,
        alternative_candidate_ids=placement.alternative_projection_ids,
        rejection_reason=decision.rejection_reason,
        policy_version=request.mapping_policy_version,
        metadata=lineage_metadata,
    )
    return RootCauseCandidateMappingResult(
        root_cause_candidate=candidate,
        source_projection_id=projection.projection_id,
        source_projection_version=projection.projection_version,
        source_candidate_id=projection.candidate_id,
        source_candidate_version=projection.candidate_version,
        mapping_policy_version=request.mapping_policy_version,
        mapping_trace=(
            "catalog references validated",
            "candidate and projection lineage preserved",
            "explicit explanation decision validated",
            "explicit placement context validated",
            "RootCauseCandidate structurally materialized",
        ),
    )


__all__ = ["MappingOutcome", "map_projection_to_root_cause_candidate"]
