from dataclasses import dataclass
from datetime import datetime, timezone

from app.decision.contracts.enums import (
    DecisionContractVersion,
    DecisionState,
    DecisionType,
)


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    candidate_reference: str
    intelligence_reference: str
    decision_type: DecisionType
    decision_state: DecisionState
    confidence: float
    created_at: datetime
    contract_version: DecisionContractVersion

    def __post_init__(self):
        if not isinstance(self.decision_id, str):
            raise TypeError(
                "decision_id must be a string"
            )

        if not self.decision_id.strip():
            raise ValueError(
                "decision_id is required"
            )

        if not isinstance(self.candidate_reference, str):
            raise TypeError(
                "candidate_reference must be a string"
            )

        if not self.candidate_reference.strip():
            raise ValueError(
                "candidate_reference is required"
            )

        if not isinstance(self.intelligence_reference, str):
            raise TypeError(
                "intelligence_reference must be a string"
            )

        if not self.intelligence_reference.strip():
            raise ValueError(
                "intelligence_reference is required"
            )

        if not isinstance(
            self.decision_type,
            DecisionType,
        ):
            raise TypeError(
                "decision_type must be DecisionType"
            )

        if not isinstance(
            self.decision_state,
            DecisionState,
        ):
            raise TypeError(
                "decision_state must be DecisionState"
            )

        if not isinstance(
            self.contract_version,
            DecisionContractVersion,
        ):
            raise TypeError(
                "contract_version must be "
                "DecisionContractVersion"
            )

        if (
            isinstance(self.confidence, bool)
            or not isinstance(
                self.confidence,
                (int, float),
            )
        ):
            raise TypeError(
                "confidence must be numeric"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        if not isinstance(self.created_at, datetime):
            raise TypeError(
                "created_at must be datetime"
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone aware"
            )

        if (
            self.created_at.utcoffset()
            != timezone.utc.utcoffset(
                self.created_at
            )
        ):
            object.__setattr__(
                self,
                "created_at",
                self.created_at.astimezone(
                    timezone.utc
                ),
            )
