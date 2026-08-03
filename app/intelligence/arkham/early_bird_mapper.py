from __future__ import annotations

from datetime import timezone

from app.intelligence.early_bird.models import (
    EarlyBirdCandidate,
)

from .models import (
    ArkhamWhaleEvent,
)


class ArkhamEarlyBirdMapper:
    """
    Maps Arkham whale intelligence
    into EarlyBird candidate contract.

    Translation only.
    No decision logic.
    """

    def map(
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
            100.0,
            event.amount_usd / 1_000_000,
        )

        return EarlyBirdCandidate(
            candidate_id=(
                f"arkham:{event.event_id}"
            ),
            asset=event.asset,
            observed_at=(
                event.observed_at.astimezone(
                    timezone.utc
                )
            ),
            source="arkham",
            quality=90.0,
            whale_activity_score=whale_score,
            open_interest_change_score=0.0,
            funding_divergence_score=0.0,
            volume_expansion_score=0.0,
            relative_strength_score=0.0,
            liquidity_event_score=0.0,
            structure_event_score=0.0,
            momentum_shift_score=0.0,
            freshness_score=100.0,
            data_completeness_score=80.0,
            fast_event_ids=(
                event.event_id,
            ),
            observation_ids=(
                f"arkham-observation:{event.event_id}",
            ),
            metadata={
                "provider": "arkham",
                "chain": event.chain.value,
                "event_type": event.event_type.value,
                "direction": event.direction.value,
                "source_entity": event.source_entity,
                "destination_entity": event.destination_entity,
            },
        )


__all__ = [
    "ArkhamEarlyBirdMapper",
]
