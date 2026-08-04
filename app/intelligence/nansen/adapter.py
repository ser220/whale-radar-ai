from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .models import SmartMoneyObservation


class NansenIntelligenceAdapter:
    """
    Boundary adapter for Nansen intelligence data.

    Converts external Nansen payloads
    into internal Whale Radar contracts.

    No ranking.
    No decision logic.
    """

    def to_smart_money_observation(
        self,
        payload: Mapping[str, Any],
    ) -> SmartMoneyObservation:

        return SmartMoneyObservation(
            asset=payload["token_symbol"],
            chain=payload["chain"],
            net_flow_24h_usd=payload["net_flow_24h_usd"],
            net_flow_7d_usd=payload["net_flow_7d_usd"],
            net_flow_30d_usd=payload["net_flow_30d_usd"],
            trader_count=payload["trader_count"],
            market_cap_usd=payload["market_cap_usd"],
            observed_at=datetime.now(
                timezone.utc
            ),
        )
