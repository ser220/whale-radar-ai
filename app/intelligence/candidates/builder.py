from datetime import datetime, timezone
from typing import Iterable, Mapping, Any, Optional

from app.intelligence.candidates.identity import (
    build_candidate_id,
)

from app.intelligence.candidates.models import (
    CandidateHypothesis,
)

from app.intelligence.candidates.enums import (
    CandidateCategory,
    CandidateStatus,
)


class CandidateBuilder:

    def __init__(
        self,
        identity_policy_version: str = "v1",
        candidate_policy_version: str = "v1",
    ):
        self.identity_policy_version = (
            identity_policy_version
        )
        self.candidate_policy_version = (
            candidate_policy_version
        )

    def build(
        self,
        *,
        category: CandidateCategory,
        subject: str,
        hypothesis_reference: str,
        description: str,
        supporting_evidence_refs: Iterable[str] = (),
        contradicting_evidence_refs: Iterable[str] = (),
        limitation_references: Iterable[str] = (),
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> CandidateHypothesis:

        candidate_id = build_candidate_id(
            subject=subject,
            category=category.value,
            hypothesis_reference=hypothesis_reference,
            identity_policy_version=(
                self.identity_policy_version
            ),
        )

        return CandidateHypothesis(
            candidate_id=candidate_id,
            candidate_version=1,
            candidate_identity_policy_version=(
                self.identity_policy_version
            ),
            candidate_policy_version=(
                self.candidate_policy_version
            ),
            category=category,
            subject=subject,
            hypothesis_reference=(
                hypothesis_reference
            ),
            description=description,
            status=CandidateStatus.CREATED,
            supporting_evidence_refs=tuple(
                supporting_evidence_refs
            ),
            contradicting_evidence_refs=tuple(
                contradicting_evidence_refs
            ),
            limitation_references=tuple(
                limitation_references
            ),
            created_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
