from datetime import datetime, timezone
from typing import Iterable

from .models import (
    CandidateCompletenessRecord,
    ProviderCompletenessRecord,
)
from .policy import CandidateCompletenessPolicy


class CandidateCompletenessEvaluator:
    """Builds aggregated completeness records for candidates."""

    @staticmethod
    def evaluate(
        candidate_id: str,
        provider_records: Iterable[ProviderCompletenessRecord],
        evaluated_at: datetime = None,
    ) -> CandidateCompletenessRecord:
        records = tuple(provider_records)

        status = CandidateCompletenessPolicy.evaluate_status(records)

        resolved_evaluated_at = (
            evaluated_at
            if evaluated_at is not None
            else datetime.now(timezone.utc)
        )

        return CandidateCompletenessRecord(
            candidate_id=candidate_id,
            provider_records=records,
            status=status,
            evaluated_at=resolved_evaluated_at,
        )
