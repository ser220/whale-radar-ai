from .enums import (
    CandidateCompatibilityStatus,
)

from .models import (
    CandidateCompatibilityRecord,
)


class CandidateCompatibilityPolicy:
    """Validation rules for compatibility records."""

    @staticmethod
    def validate(
        record: CandidateCompatibilityRecord,
    ) -> CandidateCompatibilityRecord:

        if not isinstance(
            record,
            CandidateCompatibilityRecord,
        ):
            raise TypeError(
                "record must be CandidateCompatibilityRecord"
            )

        if not isinstance(
            record.status,
            CandidateCompatibilityStatus,
        ):
            raise TypeError(
                "invalid compatibility status"
            )

        if not record.candidate_reference:
            raise ValueError(
                "candidate_reference required"
            )

        return record

