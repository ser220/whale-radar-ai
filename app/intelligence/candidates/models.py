from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Tuple

from app.intelligence.candidates.enums import (
    CandidateCategory,
    CandidateStatus,
)


@dataclass(frozen=True)
class CandidateHypothesis:
    candidate_id: str
    candidate_version: int

    candidate_identity_policy_version: str
    candidate_policy_version: str

    category: CandidateCategory
    subject: str

    hypothesis_reference: str
    description: str

    status: CandidateStatus

    supporting_evidence_refs: Tuple[str, ...] = field(
        default_factory=tuple
    )

    contradicting_evidence_refs: Tuple[str, ...] = field(
        default_factory=tuple
    )

    limitation_references: Tuple[str, ...] = field(
        default_factory=tuple
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id is required")

        if self.candidate_version < 1:
            raise ValueError(
                "candidate_version must be positive"
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone aware"
            )

        object.__setattr__(
            self,
            "created_at",
            self.created_at.astimezone(timezone.utc),
        )

        object.__setattr__(
            self,
            "supporting_evidence_refs",
            tuple(self.supporting_evidence_refs),
        )

        object.__setattr__(
            self,
            "contradicting_evidence_refs",
            tuple(self.contradicting_evidence_refs),
        )

        object.__setattr__(
            self,
            "limitation_references",
            tuple(self.limitation_references),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_version": self.candidate_version,
            "candidate_identity_policy_version":
                self.candidate_identity_policy_version,
            "candidate_policy_version":
                self.candidate_policy_version,
            "category": self.category.value,
            "subject": self.subject,
            "hypothesis_reference":
                self.hypothesis_reference,
            "description": self.description,
            "status": self.status.value,
            "supporting_evidence_refs":
                list(self.supporting_evidence_refs),
            "contradicting_evidence_refs":
                list(self.contradicting_evidence_refs),
            "limitation_references":
                list(self.limitation_references),
            "created_at":
                self.created_at.isoformat(),
            "metadata":
                dict(self.metadata),
        }
