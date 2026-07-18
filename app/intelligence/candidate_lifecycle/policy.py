from app.intelligence.candidate_lifecycle.enums import (
    CandidateLifecycleState,
)


_ALLOWED_TRANSITIONS = {
    CandidateLifecycleState.CREATED: {
        CandidateLifecycleState.ACTIVE,
        CandidateLifecycleState.EXPIRED,
    },
    CandidateLifecycleState.ACTIVE: {
        CandidateLifecycleState.UPDATED,
        CandidateLifecycleState.SUPERSEDED,
        CandidateLifecycleState.EXPIRED,
    },
    CandidateLifecycleState.UPDATED: {
        CandidateLifecycleState.ACTIVE,
        CandidateLifecycleState.SUPERSEDED,
        CandidateLifecycleState.EXPIRED,
    },
    CandidateLifecycleState.SUPERSEDED: set(),
    CandidateLifecycleState.EXPIRED: set(),
}


class CandidateLifecyclePolicy:

    @staticmethod
    def can_transition(
        current: CandidateLifecycleState,
        target: CandidateLifecycleState,
    ) -> bool:
        return target in _ALLOWED_TRANSITIONS.get(
            current,
            set(),
        )

    @staticmethod
    def validate_transition(
        current: CandidateLifecycleState,
        target: CandidateLifecycleState,
    ) -> None:
        if not CandidateLifecyclePolicy.can_transition(
            current,
            target,
        ):
            raise ValueError(
                "invalid candidate lifecycle transition: "
                f"{current.value} -> {target.value}"
            )
