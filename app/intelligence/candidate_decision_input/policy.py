from .enums import (
    CandidateDecisionInputStatus,
)

from .models import (
    CandidateDecisionInputProjection,
)


class CandidateDecisionInputPolicy:
    """Validation rules for decision input projections."""

    @staticmethod
    def validate(
        projection: CandidateDecisionInputProjection,
    ) -> CandidateDecisionInputProjection:

        if not isinstance(
            projection,
            CandidateDecisionInputProjection,
        ):
            raise TypeError(
                "projection must be CandidateDecisionInputProjection"
            )

        if not isinstance(
            projection.status,
            CandidateDecisionInputStatus,
        ):
            raise TypeError(
                "invalid decision input status"
            )

        if not projection.intelligence_reference:
            raise ValueError(
                "intelligence_reference required"
            )

        return projection
