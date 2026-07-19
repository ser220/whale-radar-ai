from datetime import datetime, timezone

from .enums import (
    CandidateProjectionStatus,
    CandidateProjectionVersion,
)

from .models import (
    CandidateIntelligenceProjection,
)

from .policy import (
    CandidateProjectionPolicy,
)


class CandidateProjectionProjector:
    """Builds immutable candidate read projections."""

    def __init__(
        self,
        version: CandidateProjectionVersion = (
            CandidateProjectionVersion.V1
        ),
    ):
        self.version = version

    def project(
        self,
        *,
        candidate_id: str,
        lifecycle_state: str,
        resolution_state: str,
        completeness_state: str,
        evidence_reference_ids: tuple[str, ...],
        attachment_reference_ids: tuple[str, ...],
        status: CandidateProjectionStatus = (
            CandidateProjectionStatus.AVAILABLE
        ),
    ) -> CandidateIntelligenceProjection:

        projection = CandidateIntelligenceProjection(
            candidate_id=candidate_id,
            lifecycle_state=lifecycle_state,
            resolution_state=resolution_state,
            completeness_state=completeness_state,
            evidence_reference_ids=(
                evidence_reference_ids
            ),
            attachment_reference_ids=(
                attachment_reference_ids
            ),
            status=status,
            version=self.version,
            created_at=datetime.now(
                timezone.utc
            ),
        )

        return CandidateProjectionPolicy.validate(
            projection
        )
