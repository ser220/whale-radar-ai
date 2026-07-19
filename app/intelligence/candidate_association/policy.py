from .enums import CandidateAssociationType


class CandidateAssociationPolicy:
    """Validation policy for candidate situation associations."""

    @staticmethod
    def validate_type(
        association_type: CandidateAssociationType,
    ) -> CandidateAssociationType:

        if not isinstance(
            association_type,
            CandidateAssociationType,
        ):
            raise TypeError(
                "association_type must be CandidateAssociationType"
            )

        return association_type

    @staticmethod
    def allows_multiple(
        association_type: CandidateAssociationType,
    ) -> bool:

        CandidateAssociationPolicy.validate_type(
            association_type
        )

        return association_type != (
            CandidateAssociationType.PRIMARY
        )
