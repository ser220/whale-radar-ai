from __future__ import annotations

from datetime import datetime, timezone

from app.decision.contracts import (
    DecisionContractVersion,
    DecisionPolicy,
    DecisionRecord,
    DecisionState,
    DecisionType,
)
from app.decision.identity import build_decision_id
from app.intelligence.candidate_decision_input.models import (
    CandidateDecisionInputProjection,
)


class DecisionBuilder:
    """
    Build an immutable DecisionRecord from a canonical
    CandidateDecisionInputProjection.
    """

    def __init__(
        self,
        contract_version: DecisionContractVersion = (
            DecisionContractVersion.V1
        ),
    ) -> None:
        if not isinstance(
            contract_version,
            DecisionContractVersion,
        ):
            raise TypeError(
                "contract_version must be "
                "DecisionContractVersion"
            )

        self._contract_version = contract_version

    def build(
        self,
        projection: CandidateDecisionInputProjection,
        decision_type: DecisionType,
        confidence: float,
        created_at: datetime | None = None,
    ) -> DecisionRecord:
        if not isinstance(
            projection,
            CandidateDecisionInputProjection,
        ):
            raise TypeError(
                "projection must be "
                "CandidateDecisionInputProjection"
            )

        if not isinstance(
            decision_type,
            DecisionType,
        ):
            raise TypeError(
                "decision_type must be DecisionType"
            )

        record_created_at = (
            created_at
            if created_at is not None
            else datetime.now(timezone.utc)
        )

        decision_id = build_decision_id(
            candidate_reference=(
                projection.candidate_reference
            ),
            intelligence_reference=(
                projection.intelligence_reference
            ),
        )

        record = DecisionRecord(
            decision_id=decision_id,
            candidate_reference=(
                projection.candidate_reference
            ),
            intelligence_reference=(
                projection.intelligence_reference
            ),
            decision_type=decision_type,
            decision_state=DecisionState.CREATED,
            confidence=confidence,
            created_at=record_created_at,
            contract_version=self._contract_version,
        )

        return DecisionPolicy.validate(record)
