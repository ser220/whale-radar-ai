from dataclasses import dataclass
from datetime import datetime, timezone

from .enums import (
    CandidateCompatibilityStatus,
    CandidateCompatibilityVersion,
)


@dataclass(frozen=True)
class CandidateCompatibilityRecord:
    """Immutable candidate intelligence compatibility record."""

    candidate_reference: str
    producer_version: str
    consumer_version: str
    status: CandidateCompatibilityStatus
    compatibility_version: CandidateCompatibilityVersion
    checked_at: datetime

    def __post_init__(self) -> None:
        candidate_reference = (
            self.candidate_reference.strip()
        )

        producer_version = (
            self.producer_version.strip()
        )

        consumer_version = (
            self.consumer_version.strip()
        )

        if not candidate_reference:
            raise ValueError(
                "candidate_reference must not be empty"
            )

        if not producer_version:
            raise ValueError(
                "producer_version must not be empty"
            )

        if not consumer_version:
            raise ValueError(
                "consumer_version must not be empty"
            )

        if self.checked_at.tzinfo is None:
            raise ValueError(
                "checked_at must be timezone-aware"
            )

        object.__setattr__(
            self,
            "candidate_reference",
            candidate_reference,
        )

        object.__setattr__(
            self,
            "producer_version",
            producer_version,
        )

        object.__setattr__(
            self,
            "consumer_version",
            consumer_version,
        )

        object.__setattr__(
            self,
            "checked_at",
            self.checked_at.astimezone(
                timezone.utc
            ),
        )
