"""Immutable representation contracts between candidates and explanations."""

from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import Any, Mapping, Tuple

from app.intelligence.reality_gap.enums import (
    RootCauseCategory,
    RootCauseDisposition,
    RootCauseRole,
)

from ._validation import (
    ProjectionValidationError,
    canonical_json_bytes,
    enum_value,
    frozen_metadata,
    mapping_payload,
    parse_datetime,
    plain,
    positive_version,
    reference_tuple,
    required_text,
    utc_datetime,
)
from .enums import ProjectionFailureCategory


@dataclass(frozen=True)
class EvidenceReferenceSnapshot:
    """Exact candidate reference relationships captured for one projection."""

    supporting_evidence_refs: Tuple[str, ...]
    contradicting_evidence_refs: Tuple[str, ...]
    limitation_references: Tuple[str, ...]

    def __post_init__(self) -> None:
        supporting = reference_tuple(
            self.supporting_evidence_refs,
            "supporting_evidence_refs",
        )
        contradicting = reference_tuple(
            self.contradicting_evidence_refs,
            "contradicting_evidence_refs",
        )
        limitations = reference_tuple(
            self.limitation_references,
            "limitation_references",
        )
        if set(supporting) & set(contradicting):
            raise ProjectionValidationError(
                ProjectionFailureCategory.INVALID_EVIDENCE_REFERENCE,
                "evidence_reference_snapshot",
                "supporting and contradicting references must be disjoint",
            )
        object.__setattr__(self, "supporting_evidence_refs", supporting)
        object.__setattr__(self, "contradicting_evidence_refs", contradicting)
        object.__setattr__(self, "limitation_references", limitations)

    def to_dict(self) -> dict:
        return {
            "supporting_evidence_refs": list(self.supporting_evidence_refs),
            "contradicting_evidence_refs": list(self.contradicting_evidence_refs),
            "limitation_references": list(self.limitation_references),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "EvidenceReferenceSnapshot":
        field_names = tuple(item.name for item in fields(cls))
        return cls(**mapping_payload(value, field_names, cls.__name__))


@dataclass(frozen=True)
class CandidateProjection:
    """One immutable candidate representation in an explanation context."""

    projection_id: str
    projection_version: int
    candidate_id: str
    candidate_version: int
    projection_policy_version: str
    analysis_context_id: str
    category: RootCauseCategory
    role: RootCauseRole
    disposition: RootCauseDisposition
    tree_context_reference: str
    evidence_reference_snapshot: EvidenceReferenceSnapshot
    created_at: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        projection_id = required_text(
            self.projection_id,
            "projection_id",
            ProjectionFailureCategory.MISSING_IDENTITY,
        )
        candidate_id = required_text(
            self.candidate_id,
            "candidate_id",
            ProjectionFailureCategory.MISSING_IDENTITY,
        )
        if projection_id == candidate_id:
            raise ProjectionValidationError(
                ProjectionFailureCategory.MISSING_IDENTITY,
                "projection_id",
                "must remain separate from candidate_id",
            )
        projection_version = positive_version(
            self.projection_version,
            "projection_version",
        )
        candidate_version = positive_version(
            self.candidate_version,
            "candidate_version",
        )
        policy_version = required_text(
            self.projection_policy_version,
            "projection_policy_version",
            ProjectionFailureCategory.INVALID_POLICY_VERSION,
        )
        analysis_context_id = required_text(
            self.analysis_context_id,
            "analysis_context_id",
            ProjectionFailureCategory.MISSING_IDENTITY,
        )
        tree_context = required_text(
            self.tree_context_reference,
            "tree_context_reference",
            ProjectionFailureCategory.INVALID_TREE_CONTEXT,
        )
        if tree_context in {projection_id, candidate_id, analysis_context_id}:
            raise ProjectionValidationError(
                ProjectionFailureCategory.INVALID_TREE_CONTEXT,
                "tree_context_reference",
                "must remain separate from candidate, projection, and analysis identities",
            )
        if not isinstance(self.evidence_reference_snapshot, EvidenceReferenceSnapshot):
            raise ProjectionValidationError(
                ProjectionFailureCategory.INVALID_EVIDENCE_REFERENCE,
                "evidence_reference_snapshot",
                "must be an EvidenceReferenceSnapshot",
            )

        category = enum_value(self.category, RootCauseCategory, "category")
        role = enum_value(self.role, RootCauseRole, "role")
        disposition = enum_value(
            self.disposition,
            RootCauseDisposition,
            "disposition",
        )
        created_at = utc_datetime(self.created_at, "created_at")
        metadata = frozen_metadata(self.metadata)
        self._validate_metadata_lineage(
            metadata,
            projection_id,
            projection_version,
            candidate_id,
            candidate_version,
            policy_version,
            analysis_context_id,
            tree_context,
        )

        object.__setattr__(self, "projection_id", projection_id)
        object.__setattr__(self, "projection_version", projection_version)
        object.__setattr__(self, "candidate_id", candidate_id)
        object.__setattr__(self, "candidate_version", candidate_version)
        object.__setattr__(self, "projection_policy_version", policy_version)
        object.__setattr__(self, "analysis_context_id", analysis_context_id)
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "disposition", disposition)
        object.__setattr__(self, "tree_context_reference", tree_context)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "metadata", metadata)

    @staticmethod
    def _validate_metadata_lineage(
        metadata: Mapping[str, Any],
        projection_id: str,
        projection_version: int,
        candidate_id: str,
        candidate_version: int,
        policy_version: str,
        analysis_context_id: str,
        tree_context: str,
    ) -> None:
        expected = {
            "projection_id": projection_id,
            "projection_version": projection_version,
            "candidate_id": candidate_id,
            "candidate_version": candidate_version,
            "projection_policy_version": policy_version,
            "analysis_context_id": analysis_context_id,
            "tree_context_reference": tree_context,
        }
        for key, expected_value in expected.items():
            if key not in metadata:
                continue
            if metadata[key] != expected_value:
                category = (
                    ProjectionFailureCategory.INVALID_POLICY_VERSION
                    if key == "projection_policy_version"
                    else ProjectionFailureCategory.VERSION_CONFLICT
                )
                raise ProjectionValidationError(
                    category,
                    "metadata.{0}".format(key),
                    "must agree with the explicit projection field",
                )

    def to_dict(self) -> dict:
        """Serialize in stable public field order using primitive values only."""
        return {
            "projection_id": self.projection_id,
            "projection_version": self.projection_version,
            "candidate_id": self.candidate_id,
            "candidate_version": self.candidate_version,
            "projection_policy_version": self.projection_policy_version,
            "analysis_context_id": self.analysis_context_id,
            "category": self.category.value,
            "role": self.role.value,
            "disposition": self.disposition.value,
            "tree_context_reference": self.tree_context_reference,
            "evidence_reference_snapshot": self.evidence_reference_snapshot.to_dict(),
            "created_at": self.created_at.isoformat(),
            "metadata": plain(self.metadata),
        }

    def to_json_bytes(self) -> bytes:
        """Return canonical UTF-8 JSON bytes for deterministic comparison."""
        return canonical_json_bytes(self.to_dict())

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CandidateProjection":
        field_names = tuple(item.name for item in fields(cls))
        payload = mapping_payload(value, field_names, cls.__name__)
        payload["created_at"] = parse_datetime(payload["created_at"], "created_at")
        payload["evidence_reference_snapshot"] = EvidenceReferenceSnapshot.from_dict(
            payload["evidence_reference_snapshot"]
        )
        return cls(**payload)


__all__ = [
    "CandidateProjection",
    "EvidenceReferenceSnapshot",
    "ProjectionValidationError",
]
