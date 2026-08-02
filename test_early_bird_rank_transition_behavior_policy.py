from datetime import datetime, timezone

from app.intelligence.early_bird.candidate_lifecycle import (
    EarlyBirdCandidateLifecycle,
)
from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)
from app.intelligence.early_bird.rank_transition_policy import (
    EarlyBirdRankTransitionPolicy,
)


NOW = datetime(
    2026,
    8,
    2,
    20,
    0,
    tzinfo=timezone.utc,
)


class Assessment:
    state = "accelerating"
    priority = "high"
    action_hint = "promote_ready"


class CriticalAssessment:
    state = "critical"
    priority = "high"
    action_hint = "downgrade_check"


def lifecycle(rank):
    return EarlyBirdCandidateLifecycle(
        asset="HYPE",
        rank=rank,
        first_seen=NOW,
        last_seen=NOW,
        observations_count=5,
    )


def test_behavior_acceleration_promotes_candidate():

    decision = EarlyBirdRankTransitionPolicy().evaluate(
        lifecycle=lifecycle(
            CandidateRank.DISCOVERY,
        ),
        observation={
            "negative_events": 0,
        },
        behavior_assessment=Assessment(),
    )

    assert decision.transition.value == "promote"


def test_critical_behavior_downgrades_candidate():

    decision = EarlyBirdRankTransitionPolicy().evaluate(
        lifecycle=lifecycle(
            CandidateRank.PRIME,
        ),
        observation={
            "negative_events": 0,
        },
        behavior_assessment=CriticalAssessment(),
    )

    assert decision.transition.value == "downgrade"
