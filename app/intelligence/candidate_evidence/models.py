from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple

from .enums import (
    EvidenceAssemblyVersion,
    EvidenceReferenceType,
)


@dataclass(frozen=True)
class EvidenceReference:
    """Immutable reference to evidence source."""

    reference_id: str
    reference_type: EvidenceReferenceType

    def __post_init__(self) -> None:
        reference_id = self.reference_id.strip()

        if not reference_id:
            raise ValueError(
                "reference_id must not be empty"
            )

        object.__setattr__(
            self,
            "reference_id",
            reference_id,
        )


@dataclass(frozen=True)
class CandidateEvidenceAssembly:
    """Immutable assembled evidence record for candidate."""

    candidate_id: str
    evidence_references: Tuple[EvidenceReference, ...]
    assembly_version: EvidenceAssemblyVersion
    assembled_at: datetime

    def __post_init__(self) -> None:
        candidate_id = self.candidate_id.strip()

        if not candidate_id:
            raise ValueError(
                "candidate_id must not be empty"
            )

        if not isinstance(
            self.evidence_references,
            tuple,
        ):
            raise TypeError(
                "evidence_references must be a tuple"
            )

        if not self.evidence_references:
            raise ValueError(
                "evidence_references must not be empty"
            )

        if self.assembled_at.tzinfo is None:
            raise ValueError(
                "assembled_at must be timezone-aware"
            )

        reference_ids = [
            reference.reference_id
            for reference in self.evidence_references
        ]

        if len(reference_ids) != len(set(reference_ids)):
            raise ValueError(
                "evidence references must be unique"
            )

        object.__setattr__(
            self,
            "candidate_id",
            candidate_id,
        )

        object.__setattr__(
            self,
            "assembled_at",
            self.assembled_at.astimezone(
                timezone.utc
            ),
        )
