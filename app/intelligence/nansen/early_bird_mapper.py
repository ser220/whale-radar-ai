from __future__ import annotations

from datetime import timezone

from app.intelligence.early_bird.models import (
    EarlyBirdCandidate,
)

from .models import (
    SmartMoneyObservation,
)


class NansenEarlyBirdMapper:
    """
    Maps Nansen smart money intelligence
    into EarlyBird candidate contract.

    Translation only.
    No ranking.
    No decision logic.
    """

    def map(
        self,
        observation: SmartMoneyObservation,
    ) -> EarlyBirdCandidate:

        if not isinstance(
            observation,
            SmartMoneyObservation,
        ):
            raise TypeError(
                "observation must be SmartMoneyObservation"
            )

        observed_at = (
            observation.observed_at.astimezone(
                timezone.utc
            )
        )

        flow_score = min(
            100.0,
            abs(
                observation.net_flow_7d_usd
            ) / 1_000_000,
        )

        return EarlyBirdCandidate(
            candidate_id=(
                f"nansen:{observation.asset}:"
                f"{int(observed_at.timestamp())}"
            ),
            asset=observation.asset,
            observed_at=observed_at,
            source="nansen",

            quality=85.0,

            whale_activity_score=0.0,

            open_interest_change_score=0.0,
            funding_divergence_score=0.0,
            volume_expansion_score=0.0,
            relative_strength_score=0.0,

            liquidity_event_score=flow_score,

            structure_event_score=flow_score,

            momentum_shift_score=0.0,

            freshness_score=100.0,

            data_completeness_score=90.0,

            fast_event_ids=(
                f"nansen:{observation.asset}",
            ),

            observation_ids=(
                f"nansen-observation:{observation.asset}",
            ),

            metadata={
                "provider": "nansen",
                "chain": observation.chain,
                "net_flow_24h_usd": (
                    observation.net_flow_24h_usd
                ),
                "net_flow_7d_usd": (
                    observation.net_flow_7d_usd
                ),
                "net_flow_30d_usd": (
                    observation.net_flow_30d_usd
                ),
                "trader_count": (
                    observation.trader_count
                ),
            },
        )


__all__ = [
    "NansenEarlyBirdMapper",
]
