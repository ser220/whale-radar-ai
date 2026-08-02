"""Candidate rank transition memory contract."""

from dataclasses import dataclass
from datetime import datetime


VALID_TRANSITIONS = {
    "PROMOTION",
    "DEMOTION",
    "REVERSAL",
    "STABLE",
}


def _validate_asset(
    value: str,
) -> str:

    if not isinstance(value, str):
        raise TypeError(
            "asset must be string"
        )

    asset = value.strip().upper()

    if not asset:
        raise ValueError(
            "asset must not be empty"
        )

    return asset


@dataclass(frozen=True)
class CandidateRankTransitionMemory:
    """
    Immutable record of candidate rank evolution.

    Keeps the path of a candidate:
    
    L1 -> L4
    L4 -> L2
    L4 -> S3 (reversal)
    """

    asset: str
    previous_rank: str
    current_rank: str
    transition_type: str
    reason: str
    timestamp: datetime

    def __post_init__(self) -> None:

        object.__setattr__(
            self,
            "asset",
            _validate_asset(
                self.asset
            ),
        )

        if not isinstance(
            self.previous_rank,
            str,
        ):
            raise TypeError(
                "previous_rank must be string"
            )

        if not isinstance(
            self.current_rank,
            str,
        ):
            raise TypeError(
                "current_rank must be string"
            )

        transition = self.transition_type.upper()

        if transition not in VALID_TRANSITIONS:
            raise ValueError(
                "invalid transition type"
            )

        object.__setattr__(
            self,
            "transition_type",
            transition,
        )

        if not isinstance(
            self.reason,
            str,
        ):
            raise TypeError(
                "reason must be string"
            )

        if not isinstance(
            self.timestamp,
            datetime,
        ):
            raise TypeError(
                "timestamp must be datetime"
            )


__all__ = [
    "CandidateRankTransitionMemory",
]
