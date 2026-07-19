from datetime import datetime, timezone
from typing import Optional

from .enums import (
    EvidenceAssemblyVersion,
)
from .models import (
    CandidateEvidenceAssembly,
    EvidenceReference,
)
from .policy import (
    CandidateEvidencePolicy,
)


class CandidateEvidenceAssembler:
    """Builds immutable candidate evidence assemblies."""

    def __init__(
        self,
        version: EvidenceAssemblyVersion = (
            EvidenceAssemblyVersion.V1
        ),
    ):
        self.version = version

    def assemble(
        self,
        *,
        candidate_id: str,
        evidence_references: tuple[EvidenceReference, ...],
        assembled_at: Optional[datetime] = None,
    ) -> CandidateEvidenceAssembly:

        validated_references = (
            CandidateEvidencePolicy
            .validate_references(
                evidence_references
            )
        )

        resolved_time = (
            assembled_at
            if assembled_at is not None
            else datetime.now(timezone.utc)
        )

        return CandidateEvidenceAssembly(
            candidate_id=candidate_id,
            evidence_references=(
                validated_references
            ),
            assembly_version=self.version,
            assembled_at=resolved_time,
        )
