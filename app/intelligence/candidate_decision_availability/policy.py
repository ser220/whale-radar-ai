from .enums import (
    CandidateDecisionInputAvailabilityStatus,
)

from .models import (
    CandidateDecisionInputAvailabilityRecord,
)


class CandidateDecisionInputAvailabilityPolicy:
    """Validation rules for decision input availability."""

    @staticmethod
    def validate(
        record: CandidateDecisionInputAvailabilityRecord,
    ) -> CandidateDecisionInputAvailabilityRecord:

        if not isinstance(
            record,
            CandidateDecisionInputAvailabilityRecord,
        ):
            raise TypeError(
                "record must be CandidateDecisionInputAvailabilityRecord"
            )

        if not isinstance(
            record.status,
            CandidateDecisionInputAvailabilityStatus,
        ):
            raise TypeError(
                "invalid availability status"
            )

        if not record.input_reference:
            raise ValueError(
                "input_reference required"
            )

        return record
