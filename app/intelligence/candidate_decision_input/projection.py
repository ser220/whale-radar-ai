from datetime import datetime, timezone
from typing import Optional

from .enums import (
    CandidateDecisionInputStatus,
    CandidateDecisionInputVersion,
)

from .models import (
    CandidateDecisionInputProjection,
)

from .policy import (
    CandidateDecisionInputPolicy,
)


class CandidateDecisionInputProjector:
    """Builds immutable decision input projections."""

    def __init__(
        self,
        version: CandidateDecisionInputVersion = (
            CandidateDecisionInputVersion.V1
        ),
    ):
        self.version = version

    def project(
        self,
        *,
        candidate_reference: str,
        intelligence_reference: str,
        status: CandidateDecisionInputStatus = (
            CandidateDecisionInputStatus.AVAILABLE
        ),
        created_at: Optional[datetime] = None,
    ) -> CandidateDecisionInputProjection:

        resolved_time = (
            created_at
            if created_at is not None
            else datetime.now(timezone.utc)
        )

        projection = CandidateDecisionInputProjection(
            candidate_reference=candidate_reference,
            intelligence_reference=intelligence_reference,
            status=status,
            version=self.version,
            created_at=resolved_time,
        )

        return CandidateDecisionInputPolicy.validate(
            projection
        )
