"""Candidate leaderboard contract."""

from dataclasses import dataclass
from datetime import datetime

from app.intelligence.early_bird.candidate_ranking_record import (
    CandidateRankingRecord,
)


@dataclass(frozen=True)
class CandidateLeaderboard:
    """
    Aggregated candidate rankings.

    Keeps separate views:

    LONG:
    continuation opportunities

    SHORT:
    bearish opportunities

    REVERSAL:
    former leaders changing direction
    """

    long_candidates: tuple[CandidateRankingRecord, ...]
    short_candidates: tuple[CandidateRankingRecord, ...]
    reversal_candidates: tuple[CandidateRankingRecord, ...]
    timestamp: datetime

    def __post_init__(self) -> None:

        for field_name in (
            "long_candidates",
            "short_candidates",
            "reversal_candidates",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                tuple,
            ):
                raise TypeError(
                    f"{field_name} must be tuple"
                )

            for item in value:
                if not isinstance(
                    item,
                    CandidateRankingRecord,
                ):
                    raise TypeError(
                        "leaderboard items "
                        "must be CandidateRankingRecord"
                    )

        if not isinstance(
            self.timestamp,
            datetime,
        ):
            raise TypeError(
                "timestamp must be datetime"
            )


__all__ = [
    "CandidateLeaderboard",
]
