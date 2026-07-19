from datetime import datetime, timezone
from typing import Optional

from .enums import (
    CandidateCompatibilityStatus,
    CandidateCompatibilityVersion,
)

from .models import (
    CandidateCompatibilityRecord,
)

from .policy import (
    CandidateCompatibilityPolicy,
)


class CandidateCompatibilityChecker:
    """Builds immutable compatibility records."""

    def __init__(
        self,
        version: CandidateCompatibilityVersion = (
            CandidateCompatibilityVersion.V1
        ),
    ):
        self.version = version

    def check(
        self,
        *,
        candidate_reference: str,
        producer_version: str,
        consumer_version: str,
        status: CandidateCompatibilityStatus = (
            CandidateCompatibilityStatus.COMPATIBLE
        ),
        checked_at: Optional[datetime] = None,
    ) -> CandidateCompatibilityRecord:

        resolved_time = (
            checked_at
            if checked_at is not None
            else datetime.now(timezone.utc)
        )

        record = CandidateCompatibilityRecord(
            candidate_reference=candidate_reference,
            producer_version=producer_version,
            consumer_version=consumer_version,
            status=status,
            compatibility_version=self.version,
            checked_at=resolved_time,
        )

        return CandidateCompatibilityPolicy.validate(
            record
        )
