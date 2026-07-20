from __future__ import annotations

from app.decision.builder import DecisionBuilder
from app.decision.contracts import (
    DecisionRecord,
    DecisionType,
)
from app.decision.lifecycle import DecisionLifecycle
from app.decision.repository import DecisionRepository
from app.intelligence.candidate_decision_input.models import (
    CandidateDecisionInputProjection,
)


class DecisionGovernance:
    """
    Orchestration boundary for Decision Domain.

    Coordinates builder, lifecycle, and repository only.
    """

    def __init__(
        self,
        builder: DecisionBuilder | None = None,
        repository: DecisionRepository | None = None,
    ) -> None:
        self._builder = (
            builder
            if builder is not None
            else DecisionBuilder()
        )

        self._repository = (
            repository
            if repository is not None
            else DecisionRepository()
        )

    def create(
        self,
        projection: CandidateDecisionInputProjection,
        decision_type: DecisionType,
        confidence: float,
    ) -> DecisionRecord:
        record = self._builder.build(
            projection=projection,
            decision_type=decision_type,
            confidence=confidence,
        )

        return self._repository.save(
            record
        )

    def get(
        self,
        decision_id: str,
    ) -> DecisionRecord | None:
        return self._repository.get(
            decision_id
        )

    def approve(
        self,
        decision_id: str,
    ) -> DecisionRecord:
        record = self._require_record(
            decision_id
        )

        updated = DecisionLifecycle.approve(
            record
        )

        return self._repository.save(
            updated
        )

    def reject(
        self,
        decision_id: str,
    ) -> DecisionRecord:
        record = self._require_record(
            decision_id
        )

        updated = DecisionLifecycle.reject(
            record
        )

        return self._repository.save(
            updated
        )

    def _require_record(
        self,
        decision_id: str,
    ) -> DecisionRecord:
        record = self._repository.get(
            decision_id
        )

        if record is None:
            raise ValueError(
                "decision not found"
            )

        return record
