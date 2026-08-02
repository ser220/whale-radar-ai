"""Leaderboard ranking aggregator."""

from app.intelligence.early_bird.candidate_leaderboard import (
    CandidateLeaderboard,
)


class LeaderboardRankingAggregator:
    """
    Builds directional leaderboards from candidate records.
    """

    def __init__(
        self,
        max_candidates: int = 10,
    ):
        if max_candidates <= 0:
            raise ValueError(
                "max_candidates must be positive"
            )

        self.max_candidates = max_candidates

    def aggregate(
        self,
        records,
    ) -> CandidateLeaderboard:

        long_candidates = []
        short_candidates = []
        reversal_candidates = []

        for record in records:

            if record.direction == "LONG":
                long_candidates.append(
                    record
                )

            elif record.direction == "SHORT":
                short_candidates.append(
                    record
                )

            elif record.direction == "REVERSAL":
                reversal_candidates.append(
                    record
                )

        return CandidateLeaderboard(
            long_candidates=tuple(
                self._sort(
                    long_candidates
                )
            ),
            short_candidates=tuple(
                self._sort(
                    short_candidates
                )
            ),
            reversal_candidates=tuple(
                self._sort(
                    reversal_candidates
                )
            ),
            timestamp=self._now(),
        )

    def _sort(
        self,
        candidates,
    ):

        return sorted(
            candidates,
            key=lambda item: (
                item.priority,
                item.score,
                item.confidence,
            ),
            reverse=True,
        )[
            : self.max_candidates
        ]

    @staticmethod
    def _now():
        from datetime import datetime, timezone

        return datetime.now(
            timezone.utc
        )


__all__ = [
    "LeaderboardRankingAggregator",
]
