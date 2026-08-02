"""Early Bird rank transition decision contract."""

from dataclasses import dataclass
from datetime import datetime, timezone

from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)

from app.intelligence.early_bird.rank_transition import (
    RankTransition,
)


def _required_text(
    value: str,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string"
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{field_name} must not be empty"
        )

    return value


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
class RankTransitionDecision:
    """
    Immutable record explaining a candidate rank change.
    """

    asset: str
    previous_rank: CandidateRank
    new_rank: CandidateRank
    transition: RankTransition
    reason: str
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "asset",
            _required_text(
                self.asset,
                "asset",
            ).upper(),
        )

        if not isinstance(
            self.previous_rank,
            CandidateRank,
        ):
            raise TypeError(
                "previous_rank must be CandidateRank"
            )

        if not isinstance(
            self.new_rank,
            CandidateRank,
        ):
            raise TypeError(
                "new_rank must be CandidateRank"
            )

        if not isinstance(
            self.transition,
            RankTransition,
        ):
            raise TypeError(
                "transition must be RankTransition"
            )

        object.__setattr__(
            self,
            "reason",
            _required_text(
                self.reason,
                "reason",
            ),
        )

        object.__setattr__(
            self,
            "created_at",
            _utc_datetime(
                self.created_at,
                "created_at",
            ),
        )


__all__ = [
    "RankTransitionDecision",
]
