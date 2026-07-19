from .enums import EvidenceReferenceType
from .models import EvidenceReference


class CandidateEvidencePolicy:
    """Validation rules for candidate evidence assembly."""

    @staticmethod
    def validate_reference(
        reference: EvidenceReference,
    ) -> EvidenceReference:

        if not isinstance(
            reference,
            EvidenceReference,
        ):
            raise TypeError(
                "reference must be EvidenceReference"
            )

        if not isinstance(
            reference.reference_type,
            EvidenceReferenceType,
        ):
            raise TypeError(
                "invalid evidence reference type"
            )

        return reference

    @staticmethod
    def validate_references(
        references: tuple[EvidenceReference, ...],
    ) -> tuple[EvidenceReference, ...]:

        if not references:
            raise ValueError(
                "references must not be empty"
            )

        for reference in references:
            CandidateEvidencePolicy.validate_reference(
                reference
            )

        return references
