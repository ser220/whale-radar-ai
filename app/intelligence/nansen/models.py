from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SmartMoneyObservation:
    """
    Immutable Smart Money intelligence observation.

    Nansen provides intelligence data only.

    No ranking.
    No decision logic.
    No execution semantics.
    """

    asset: str
    chain: str

    net_flow_24h_usd: float
    net_flow_7d_usd: float
    net_flow_30d_usd: float

    trader_count: int
    market_cap_usd: float

    observed_at: datetime

    def __post_init__(self) -> None:
        asset = self.asset.strip().upper()
        chain = self.chain.strip().lower()

        if not asset:
            raise ValueError(
                "asset is required"
            )

        if not chain:
            raise ValueError(
                "chain is required"
            )

        if self.trader_count < 0:
            raise ValueError(
                "trader_count cannot be negative"
            )

        if self.market_cap_usd < 0:
            raise ValueError(
                "market_cap_usd cannot be negative"
            )

        object.__setattr__(
            self,
            "asset",
            asset,
        )

        object.__setattr__(
            self,
            "chain",
            chain,
        )
