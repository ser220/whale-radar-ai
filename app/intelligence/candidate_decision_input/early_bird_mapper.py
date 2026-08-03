from __future__ import annotations

from app.intelligence.candidate_decision_input import (
    CandidateDecisionInputProjection,
    CandidateDecisionInputProjector,
)

from app.intelligence.early_bird.models import (
    EarlyBirdCandidate,
)


class EarlyBirdDecisionInputMapper:
    """
    Maps EarlyBirdCandidate into decision input boundary.

    Translation only.
    No decision logic.
    """

    def __init__(self) -> None:
        self._projector = CandidateDecisionInputProjector()

    def from_candidate(
        self,
        candidate: EarlyBirdCandidate,
    ) -> CandidateDecisionInputProjection:

        if not isinstance(
            candidate,
            EarlyBirdCandidate,
        ):
            raise TypeError(
                "candidate must be EarlyBirdCandidate"
            )

        return self._projector.project(
            candidate_reference=candidate.candidate_id,
            intelligence_reference=(
                f"early_bird:{candidate.candidate_id}"
            ),
            created_at=candidate.observed_at,
        )
