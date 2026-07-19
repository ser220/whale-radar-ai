from datetime import datetime, timezone
from typing import Optional

from .enums import (
    CandidateConsumerStatus,
    CandidateConsumerVersion,
)

from .models import (
    CandidateIntelligenceReadContract,
)

from .policy import (
    CandidateConsumerPolicy,
)


class CandidateIntelligenceConsumer:
    """Builds immutable candidate read contracts."""

    def __init__(
        self,
        version: CandidateConsumerVersion = (
            CandidateConsumerVersion.V1
        ),
    ):
        self.version = version

    def consume(
        self,
        *,
        consumer_id: str,
        envelope_reference: str,
        status: CandidateConsumerStatus = (
            CandidateConsumerStatus.AVAILABLE
        ),
        created_at: Optional[datetime] = None,
    ) -> CandidateIntelligenceReadContract:

        resolved_time = (
            created_at
            if created_at is not None
            else datetime.now(timezone.utc)
        )

        contract = CandidateIntelligenceReadContract(
            consumer_id=consumer_id,
            envelope_reference=envelope_reference,
            status=status,
            version=self.version,
            created_at=resolved_time,
        )

        return CandidateConsumerPolicy.validate(
            contract
        )
