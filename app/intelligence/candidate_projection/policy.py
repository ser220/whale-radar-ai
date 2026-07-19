from .enums import (
    CandidateProjectionStatus,
)
from .models import (
    CandidateIntelligenceProjection,
)


class CandidateProjectionPolicy:
    """Validation rules for read projections."""

    @staticmethod
    def validate(
        projection: CandidateIntelligenceProjection,
    ) -> CandidateIntelligenceProjection:

        if not isinstance(
            projection,
            CandidateIntelligenceProjection,
        ):
            raise TypeError(
                "projection must be CandidateIntelligenceProjection"
            )

        if not isinstance(
            projection.status,
            CandidateProjectionStatus,
        ):
            raise TypeError(
                "invalid projection status"
            )

        if not projection.candidate_id:
            raise ValueError(
                "candidate_id required"
            )

        return projection
