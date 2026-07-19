from .enums import (
    CandidateEnvelopeStatus,
)

from .models import (
    CandidateIntelligenceEnvelope,
)


class CandidateEnvelopePolicy:
    """Validation rules for candidate envelopes."""

    @staticmethod
    def validate(
        envelope: CandidateIntelligenceEnvelope,
    ) -> CandidateIntelligenceEnvelope:

        if not isinstance(
            envelope,
            CandidateIntelligenceEnvelope,
        ):
            raise TypeError(
                "envelope must be CandidateIntelligenceEnvelope"
            )

        if not isinstance(
            envelope.status,
            CandidateEnvelopeStatus,
        ):
            raise TypeError(
                "invalid envelope status"
            )

        if not envelope.projection_reference:
            raise ValueError(
                "projection_reference required"
            )

        return envelope
