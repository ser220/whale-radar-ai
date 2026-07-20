from __future__ import annotations

from typing import Dict, Optional

from app.decision.contracts import DecisionRecord


class DecisionRepository:
    """
    In-memory repository for immutable DecisionRecord objects.

    Storage boundary only.
    No decision logic is allowed.
    """

    def __init__(self) -> None:
        self._records: Dict[str, DecisionRecord] = {}

    def save(
        self,
        record: DecisionRecord,
    ) -> DecisionRecord:
        if not isinstance(
            record,
            DecisionRecord,
        ):
            raise TypeError(
                "record must be DecisionRecord"
            )

        self._records[
            record.decision_id
        ] = record

        return record

    def get(
        self,
        decision_id: str,
    ) -> Optional[DecisionRecord]:
        return self._records.get(
            decision_id
        )

    def exists(
        self,
        decision_id: str,
    ) -> bool:
        return (
            decision_id
            in self._records
        )
