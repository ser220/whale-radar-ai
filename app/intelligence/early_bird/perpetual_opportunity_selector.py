"""Perpetual opportunity selector."""

from app.intelligence.early_bird.perpetual_opportunity import (
    PerpetualOpportunity,
)


class PerpetualOpportunitySelector:
    """
    Selects highest priority perpetual opportunity.

    Priority:

    REVERSAL
        >
    SHORT
        >
    LONG
    """

    def select(
        self,
        leaderboard,
    ):

        candidate = self._best(
            leaderboard.reversal_candidates
        )

        if candidate:
            return self._build(
                candidate,
                "REVERSAL",
            )

        candidate = self._best(
            leaderboard.short_candidates
        )

        if candidate:
            return self._build(
                candidate,
                "CONTINUATION",
            )

        candidate = self._best(
            leaderboard.long_candidates
        )

        if candidate:
            return self._build(
                candidate,
                "CONTINUATION",
            )

        return None

    @staticmethod
    def _best(
        candidates,
    ):

        if not candidates:
            return None

        return sorted(
            candidates,
            key=lambda item: (
                item.priority,
                item.score,
                item.confidence,
            ),
            reverse=True,
        )[0]

    @staticmethod
    def _build(
        candidate,
        setup_type,
    ):

        direction = (
            "SHORT"
            if candidate.direction == "REVERSAL"
            else candidate.direction
        )

        reason = (
            "former long leader reversed bearish"
            if setup_type == "REVERSAL"
            else "highest ranked candidate"
        )

        return PerpetualOpportunity(
            asset=candidate.asset,
            direction=direction,
            setup_type=setup_type,
            rank=candidate.rank,
            score=candidate.score,
            priority=candidate.priority,
            confidence=candidate.confidence,
            reason=reason,
        )


__all__ = [
    "PerpetualOpportunitySelector",
]
