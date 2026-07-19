from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple

from .enums import (
    CandidateCompletenessStatus,
    ProviderCompletenessStatus,
)


@dataclass(frozen=True)
class ProviderCompletenessRecord:
    """Completeness record for one provider contribution."""

    provider_name: str
    status: ProviderCompletenessStatus
    checked_at: datetime
    missing_fields: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        provider_name = self.provider_name.strip()

        if not provider_name:
            raise ValueError("provider_name must not be empty")

        if self.checked_at.tzinfo is None:
            raise ValueError("checked_at must be timezone-aware")

        if not isinstance(self.missing_fields, tuple):
            raise TypeError("missing_fields must be a tuple")

        normalized_missing_fields = tuple(
            field.strip()
            for field in self.missing_fields
            if field.strip()
        )

        object.__setattr__(self, "provider_name", provider_name)
        object.__setattr__(
            self,
            "checked_at",
            self.checked_at.astimezone(timezone.utc),
        )
        object.__setattr__(
            self,
            "missing_fields",
            normalized_missing_fields,
        )


@dataclass(frozen=True)
class CandidateCompletenessRecord:
    """Aggregated completeness record for one candidate."""

    candidate_id: str
    provider_records: Tuple[ProviderCompletenessRecord, ...]
    status: CandidateCompletenessStatus
    evaluated_at: datetime

    def __post_init__(self) -> None:
        candidate_id = self.candidate_id.strip()

        if not candidate_id:
            raise ValueError("candidate_id must not be empty")

        if not isinstance(self.provider_records, tuple):
            raise TypeError("provider_records must be a tuple")

        if not self.provider_records:
            raise ValueError("provider_records must not be empty")

        if self.evaluated_at.tzinfo is None:
            raise ValueError("evaluated_at must be timezone-aware")

        provider_names = [
            record.provider_name
            for record in self.provider_records
        ]

        if len(provider_names) != len(set(provider_names)):
            raise ValueError("provider_records must contain unique providers")

        object.__setattr__(self, "candidate_id", candidate_id)
        object.__setattr__(
            self,
            "evaluated_at",
            self.evaluated_at.astimezone(timezone.utc),
        )
