from dataclasses import dataclass
from datetime import datetime, timezone

from .enums import (
    CandidateConsumerStatus,
    CandidateConsumerVersion,
)


@dataclass(frozen=True)
class CandidateIntelligenceReadContract:
    """Immutable consumer read contract."""

    consumer_id: str
    envelope_reference: str
    status: CandidateConsumerStatus
    version: CandidateConsumerVersion
    created_at: datetime

    def __post_init__(self) -> None:
        consumer_id = self.consumer_id.strip()
        envelope_reference = (
            self.envelope_reference.strip()
        )

        if not consumer_id:
            raise ValueError(
                "consumer_id must not be empty"
            )

        if not envelope_reference:
            raise ValueError(
                "envelope_reference must not be empty"
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware"
            )

        object.__setattr__(
            self,
            "consumer_id",
            consumer_id,
        )

        object.__setattr__(
            self,
            "envelope_reference",
            envelope_reference,
        )

        object.__setattr__(
            self,
            "created_at",
            self.created_at.astimezone(
                timezone.utc
            ),
        )
