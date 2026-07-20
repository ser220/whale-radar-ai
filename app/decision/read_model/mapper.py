from __future__ import annotations

from app.decision.contracts import (
    DecisionRecord,
)

from .models import DecisionReadModel


class DecisionReadModelMapper:
    """
    Maps internal DecisionRecord into external read model.
    """

    @staticmethod
    def from_record(
        record: DecisionRecord,
    ) -> DecisionReadModel:
        if not isinstance(
            record,
            DecisionRecord,
        ):
            raise TypeError(
                "record must be DecisionRecord"
            )

        return DecisionReadModel(
            decision_id=record.decision_id,
            decision_type=record.decision_type,
            decision_state=record.decision_state,
            confidence=record.confidence,
            created_at=record.created_at,
        )
