from __future__ import annotations

from typing import List

from app.decision.read_model import (
    DecisionReadModelMapper,
    DecisionReadModel,
)
from app.decision.repository import (
    DecisionRepository,
)


class DecisionQueryService:
    """
    Read-only query boundary for Decision Domain.

    Provides DecisionReadModel objects only.
    """

    def __init__(
        self,
        repository: DecisionRepository | None = None,
    ) -> None:
        self._repository = (
            repository
            if repository is not None
            else DecisionRepository()
        )

    def get(
        self,
        decision_id: str,
    ) -> DecisionReadModel | None:
        record = self._repository.get(
            decision_id
        )

        if record is None:
            return None

        return (
            DecisionReadModelMapper
            .from_record(record)
        )

    def list_by_candidate(
        self,
        candidate_reference: str,
    ) -> List[DecisionReadModel]:
        records = (
            self._repository.list_all()
        )

        return [
            DecisionReadModelMapper.from_record(
                record
            )
            for record in records
            if (
                record.candidate_reference
                == candidate_reference
            )
        ]
