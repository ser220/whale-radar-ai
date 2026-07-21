from __future__ import annotations

from app.decision.contracts import (
    DecisionType,
    DecisionRecord,
)
from app.decision.external_contract import (
    DecisionResponse,
    DecisionResponseMapper,
)
from app.decision.governance import (
    DecisionGovernance,
)
from app.decision.query import (
    DecisionQueryService,
)
from app.intelligence.candidate_decision_input.models import (
    CandidateDecisionInputProjection,
)


class DecisionApplicationService:
    """
    Application boundary for external consumers.

    Coordinates commands and queries only.
    """

    def __init__(
        self,
        governance: DecisionGovernance | None = None,
        query_service: DecisionQueryService | None = None,
    ) -> None:
        self._governance = (
            governance
            if governance is not None
            else DecisionGovernance()
        )

        self._query_service = (
            query_service
            if query_service is not None
            else DecisionQueryService()
        )

    def create_decision(
        self,
        projection: CandidateDecisionInputProjection,
        decision_type: DecisionType,
        confidence: float,
    ) -> DecisionResponse:
        record = (
            self._governance.create(
                projection=projection,
                decision_type=decision_type,
                confidence=confidence,
            )
        )

        return (
            DecisionResponseMapper
            .from_record(record)
        )

    def get_decision(
        self,
        decision_id: str,
    ) -> DecisionResponse | None:
        read_model = (
            self._query_service.get(
                decision_id
            )
        )

        if read_model is None:
            return None

        return DecisionResponse(
            decision_id=read_model.decision_id,
            decision_type=read_model.decision_type,
            decision_state=read_model.decision_state,
            confidence=read_model.confidence,
            created_at=read_model.created_at,
        )

    def approve_decision(
        self,
        decision_id: str,
    ) -> DecisionResponse:
        record = (
            self._governance.approve(
                decision_id
            )
        )

        return (
            DecisionResponseMapper
            .from_record(record)
        )

    def reject_decision(
        self,
        decision_id: str,
    ) -> DecisionResponse:
        record = (
            self._governance.reject(
                decision_id
            )
        )

        return (
            DecisionResponseMapper
            .from_record(record)
        )
