from datetime import datetime, timezone

from app.intelligence.candidate_lifecycle.enums import (
    CandidateLifecycleState,
)

from app.intelligence.candidate_lifecycle.models import (
    CandidateLifecycleRecord,
)

from app.intelligence.candidate_lifecycle.policy import (
    CandidateLifecyclePolicy,
)


class CandidateLifecycleManager:

    def create(
        self,
        candidate_id: str,
        state: CandidateLifecycleState = (
            CandidateLifecycleState.CREATED
        ),
    ) -> CandidateLifecycleRecord:

        return CandidateLifecycleRecord(
            candidate_id=candidate_id,
            state=state,
            changed_at=datetime.now(timezone.utc),
        )

    def transition(
        self,
        record: CandidateLifecycleRecord,
        target: CandidateLifecycleState,
        reason: str = "",
    ) -> CandidateLifecycleRecord:

        CandidateLifecyclePolicy.validate_transition(
            record.state,
            target,
        )

        return CandidateLifecycleRecord(
            candidate_id=record.candidate_id,
            state=target,
            previous_state=record.state,
            changed_at=datetime.now(timezone.utc),
            reason=reason,
        )
