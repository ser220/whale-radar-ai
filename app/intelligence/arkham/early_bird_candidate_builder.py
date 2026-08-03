from __future__ import annotations

from app.intelligence.early_bird.models import (
    EarlyBirdCandidate,
)

from .models import ArkhamWhaleEvent


class ArkhamEarlyBirdCandidateBuilder:
    """
    Converts Arkham whale events
    into EarlyBird candidates.

    Translation only.
    No decision logic.
    """

    def build(
        self,
        event: ArkhamWhaleEvent,
    ) -> EarlyBirdCandidate:

        if not isinstance(
            event,
            ArkhamWhaleEvent,
        ):
            raise TypeError(
                "event must be ArkhamWhaleEvent"
            )

        whale_score = min(
            event.amount_usd / 1_000_000,
            100,
        )

        return EarlyBirdCandidate(
            candidate_id=(
                f"arkham:{event.event_id}"
            ),
            asset=event.asset,
            observed_at=event.observed_at,
            source="arkham",
            quality=90,
            whale_activity_score=whale_score,
            open_interest_change_score=0,
            funding_divergence_score=0,
            volume_expansion_score=0,
            relative_strength_score=0,
            liquidity_event_score=whale_score,
            structure_event_score=0,
            momentum_shift_score=0,
            freshness_score=95,
            data_completeness_score=80,
            fast_event_ids=(
                event.event_id,
            ),
            observation_ids=(
                f"arkham-observation:{event.event_id}",
            ),
            metadata={
                "chain": event.chain.value,
                "event_type": event.event_type.value,
                "direction": event.direction.value,
                "amount_usd": event.amount_usd,
                "source_entity": event.source_entity,
                "destination_entity": event.destination_entity,
            },
        )


__all__ = [
    "ArkhamEarlyBirdCandidateBuilder",
]
