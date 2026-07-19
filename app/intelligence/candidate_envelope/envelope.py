from datetime import datetime, timezone
from typing import Optional

from .enums import (
    CandidateEnvelopeStatus,
    CandidateEnvelopeVersion,
)

from .models import (
    CandidateIntelligenceEnvelope,
)

from .policy import (
    CandidateEnvelopePolicy,
)


class CandidateEnvelopeBuilder:
    """Builds immutable candidate intelligence envelopes."""

    def __init__(
        self,
        version: CandidateEnvelopeVersion = (
            CandidateEnvelopeVersion.V1
        ),
    ):
        self.version = version

    def build(
        self,
        *,
        envelope_id: str,
        candidate_id: str,
        projection_reference: str,
        status: CandidateEnvelopeStatus = (
            CandidateEnvelopeStatus.AVAILABLE
        ),
        created_at: Optional[datetime] = None,
    ) -> CandidateIntelligenceEnvelope:

        resolved_time = (
            created_at
            if created_at is not None
            else datetime.now(timezone.utc)
        )

        envelope = CandidateIntelligenceEnvelope(
            envelope_id=envelope_id,
            candidate_id=candidate_id,
            projection_reference=projection_reference,
            status=status,
            version=self.version,
            created_at=resolved_time,
        )

        return CandidateEnvelopePolicy.validate(
            envelope
        )
