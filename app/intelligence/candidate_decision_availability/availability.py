from datetime import datetime, timezone
from typing import Optional

from .enums import (
    CandidateDecisionInputAvailabilityStatus,
    CandidateDecisionInputAvailabilityVersion,
)

from .models import (
    CandidateDecisionInputAvailabilityRecord,
)

from .policy import (
    CandidateDecisionInputAvailabilityPolicy,
)


class CandidateDecisionInputAvailabilityChecker:
    """Builds immutable availability records."""

    def __init__(
        self,
        version: CandidateDecisionInputAvailabilityVersion = (
            CandidateDecisionInputAvailabilityVersion.V1
        ),
    ):
        self.version = version

    def check(
        self,
        *,
        input_reference: str,
        status: CandidateDecisionInputAvailabilityStatus = (
            CandidateDecisionInputAvailabilityStatus.AVAILABLE
        ),
        checked_at: Optional[datetime] = None,
    ) -> CandidateDecisionInputAvailabilityRecord:

        resolved_time = (
            checked_at
            if checked_at is not None
            else datetime.now(timezone.utc)
        )

        record = CandidateDecisionInputAvailabilityRecord(
            input_reference=input_reference,
            status=status,
            version=self.version,
            checked_at=resolved_time,
        )

        return CandidateDecisionInputAvailabilityPolicy.validate(
            record
        )
