"""Early Bird candidate lifecycle state contract."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Tuple

from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)
from app.intelligence.early_bird.rank_transition_decision import (
    RankTransitionDecision,
)


def _required_asset(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            "asset must be a string"
        )

    value = value.strip()

    if not value:
        raise ValueError(
            "asset must not be empty"
        )

    return value.upper()


def _utc_datetime(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None:
        raise ValueError(
            f"{field_name} must be timezone aware"
        )

    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class EarlyBirdCandidateLifecycle:
    """
    Persistent lifecycle state of one candidate.
    """

    asset: str
    rank: CandidateRank
    first_seen: datetime
    last_seen: datetime
    observations_count: int = 0
    rank_history: Tuple[CandidateRank, ...] = field(
        default_factory=tuple
    )
    transition_history: Tuple[
        RankTransitionDecision,
        ...,
    ] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "asset",
            _required_asset(self.asset),
        )

        if not isinstance(
            self.rank,
            CandidateRank,
        ):
            raise TypeError(
                "rank must be CandidateRank"
            )

        object.__setattr__(
            self,
            "first_seen",
            _utc_datetime(
                self.first_seen,
                "first_seen",
            ),
        )

        object.__setattr__(
            self,
            "last_seen",
            _utc_datetime(
                self.last_seen,
                "last_seen",
            ),
        )

        if self.last_seen < self.first_seen:
            raise ValueError(
                "last_seen must not be before first_seen"
            )

        if (
            isinstance(
                self.observations_count,
                bool,
            )
            or not isinstance(
                self.observations_count,
                int,
            )
        ):
            raise TypeError(
                "observations_count must be integer"
            )

        if self.observations_count < 0:
            raise ValueError(
                "observations_count must not be negative"
            )

        history = self.rank_history

        if not history:
            history = (
                self.rank,
            )

        if not all(
            isinstance(
                item,
                CandidateRank,
            )
            for item in history
        ):
            raise TypeError(
                "rank_history must contain CandidateRank values"
            )

        if history[-1] != self.rank:
            raise ValueError(
                "rank_history must end with current rank"
            )

        object.__setattr__(
            self,
            "rank_history",
            tuple(history),
        )

        transition_history = tuple(
            self.transition_history
        )

        if not all(
            isinstance(
                item,
                RankTransitionDecision,
            )
            for item in transition_history
        ):
            raise TypeError(
                "transition_history must contain "
                "RankTransitionDecision values"
            )

        if any(
            item.asset != self.asset
            for item in transition_history
        ):
            raise ValueError(
                "transition_history assets must "
                "match lifecycle asset"
            )

        object.__setattr__(
            self,
            "transition_history",
            transition_history,
        )


__all__ = [
    "EarlyBirdCandidateLifecycle",
]
