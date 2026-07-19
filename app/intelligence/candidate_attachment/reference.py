from datetime import datetime, timezone
from typing import Optional

from .enums import (
    CandidateAttachmentType,
    CandidateAttachmentReferenceVersion,
)

from .models import (
    CandidateAttachmentReference,
)

from .policy import (
    CandidateAttachmentReferencePolicy,
)


class CandidateAttachmentReferenceBuilder:
    """Builds immutable candidate attachment references."""

    def __init__(
        self,
        version: CandidateAttachmentReferenceVersion = (
            CandidateAttachmentReferenceVersion.V1
        ),
    ):
        self.version = version

    def build(
        self,
        *,
        candidate_id: str,
        attachment_id: str,
        attachment_type: CandidateAttachmentType,
        created_at: Optional[datetime] = None,
    ) -> CandidateAttachmentReference:

        resolved_time = (
            created_at
            if created_at is not None
            else datetime.now(timezone.utc)
        )

        reference = CandidateAttachmentReference(
            candidate_id=candidate_id,
            attachment_id=attachment_id,
            attachment_type=attachment_type,
            reference_version=self.version,
            created_at=resolved_time,
        )

        return CandidateAttachmentReferencePolicy.validate(
            reference
        )
