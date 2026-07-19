from .enums import (
    CandidateConsumerStatus,
)

from .models import (
    CandidateIntelligenceReadContract,
)


class CandidateConsumerPolicy:
    """Validation rules for consumer contracts."""

    @staticmethod
    def validate(
        contract: CandidateIntelligenceReadContract,
    ) -> CandidateIntelligenceReadContract:

        if not isinstance(
            contract,
            CandidateIntelligenceReadContract,
        ):
            raise TypeError(
                "contract must be CandidateIntelligenceReadContract"
            )

        if not isinstance(
            contract.status,
            CandidateConsumerStatus,
        ):
            raise TypeError(
                "invalid consumer status"
            )

        if not contract.envelope_reference:
            raise ValueError(
                "envelope_reference required"
            )

        return contract
