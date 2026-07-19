from datetime import datetime, timezone
from typing import Optional

from .enums import (
    AssociationReferenceVersion,
    CandidateAssociationType,
)
from .models import (
    CandidateSituationAssociation,
)


class CandidateAssociationBuilder:
    """Builds immutable candidate situation associations."""

    def __init__(
        self,
        reference_version: AssociationReferenceVersion = (
            AssociationReferenceVersion.V1
        ),
    ):
        self.reference_version = reference_version

    def build(
        self,
        *,
        candidate_id: str,
        situation_event_id: str,
        association_type: CandidateAssociationType,
        created_at: Optional[datetime] = None,
    ) -> CandidateSituationAssociation:

        if not isinstance(
            association_type,
            CandidateAssociationType,
        ):
            raise TypeError(
                "association_type must be CandidateAssociationType"
            )

        resolved_created_at = (
            created_at
            if created_at is not None
            else datetime.now(timezone.utc)
        )

        return CandidateSituationAssociation(
            candidate_id=candidate_id,
            situation_event_id=situation_event_id,
            association_type=association_type,
            reference_version=self.reference_version,
            created_at=resolved_created_at,
        )
