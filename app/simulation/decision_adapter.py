from __future__ import annotations

from app.decision.application import (
    DecisionApplicationService,
)

from app.decision.contracts import (
    DecisionType,
)

from app.intelligence.candidate_decision_input.models import (
    CandidateDecisionInputProjection,
)


class SimulationDecisionAdapter:
    """
    Connects simulation snapshots
    with decision application boundary.
    """

    def __init__(
        self,
        application_service: DecisionApplicationService | None = None,
    ) -> None:

        self._application_service = (
            application_service
            if application_service is not None
            else DecisionApplicationService()
        )

    def create_decision(
        self,
        projection: CandidateDecisionInputProjection,
        confidence: float,
    ):
        return (
            self._application_service
            .create_decision(
                projection=projection,
                decision_type=DecisionType.LONG,
                confidence=confidence,
            )
        )
