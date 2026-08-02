"""Policy layer for candidate behaviour interpretation."""

from dataclasses import dataclass

from app.intelligence.early_bird.candidate_behavior_score import (
    CandidateBehaviorScore,
)


@dataclass(frozen=True)
class CandidateBehaviorAssessment:
    """Interpreted candidate behaviour state."""

    asset: str
    state: str
    priority: str
    action_hint: str


class CandidateBehaviorPolicy:
    """
    Converts behaviour score into operational assessment.
    """

    def evaluate(
        self,
        score: CandidateBehaviorScore,
    ) -> CandidateBehaviorAssessment:

        if not isinstance(
            score,
            CandidateBehaviorScore,
        ):
            raise TypeError(
                "score must be CandidateBehaviorScore"
            )

        if (
            score.behavior_direction
            == "strengthening"
            and score.strength_score >= 70
            and score.confidence >= 60
        ):
            return CandidateBehaviorAssessment(
                asset=score.asset,
                state="accelerating",
                priority="high",
                action_hint="promote_ready",
            )

        if (
            score.behavior_direction
            == "weakening"
            and score.decay_score >= 60
            and score.confidence >= 60
        ):
            return CandidateBehaviorAssessment(
                asset=score.asset,
                state="critical",
                priority="high",
                action_hint="downgrade_check",
            )

        if (
            score.behavior_direction
            == "weakening"
        ):
            return CandidateBehaviorAssessment(
                asset=score.asset,
                state="degrading",
                priority="medium",
                action_hint="monitor",
            )

        return CandidateBehaviorAssessment(
            asset=score.asset,
            state="stable",
            priority="low",
            action_hint="monitor",
        )


__all__ = [
    "CandidateBehaviorPolicy",
    "CandidateBehaviorAssessment",
]
