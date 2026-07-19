from .enums import (
    CandidateAttachmentType,
)
from .models import (
    CandidateAttachmentReference,
)


class CandidateAttachmentReferencePolicy:
    """Validation rules for candidate attachment references."""

    @staticmethod
    def validate(
        reference: CandidateAttachmentReference,
    ) -> CandidateAttachmentReference:

        if not isinstance(
            reference,
            CandidateAttachmentReference,
        ):
            raise TypeError(
                "reference must be CandidateAttachmentReference"
            )

        if not isinstance(
            reference.attachment_type,
            CandidateAttachmentType,
        ):
            raise TypeError(
                "invalid attachment type"
            )

        return reference
