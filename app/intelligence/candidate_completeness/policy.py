from typing import Iterable

from .enums import (
    CandidateCompletenessStatus,
    ProviderCompletenessStatus,
)
from .models import ProviderCompletenessRecord


class CandidateCompletenessPolicy:
    """Deterministic policy for aggregated provider completeness."""

    @staticmethod
    def evaluate_status(
        provider_records: Iterable[ProviderCompletenessRecord],
    ) -> CandidateCompletenessStatus:
        records = tuple(provider_records)

        if not records:
            raise ValueError("provider_records must not be empty")

        statuses = tuple(record.status for record in records)

        if all(
            status is ProviderCompletenessStatus.AVAILABLE
            for status in statuses
        ):
            return CandidateCompletenessStatus.COMPLETE

        if all(
            status is ProviderCompletenessStatus.MISSING
            for status in statuses
        ):
            return CandidateCompletenessStatus.INCOMPLETE

        return CandidateCompletenessStatus.PARTIAL
