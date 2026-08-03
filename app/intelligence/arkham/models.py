from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .enums import (
    ArkhamChain,
    ArkhamFlowDirection,
    ArkhamEventType,
)


@dataclass(frozen=True)
class ArkhamWhaleEvent:
    """
    Immutable Arkham on-chain intelligence event.

    Represents whale activity only.
    No trading decision logic.
    """

    event_id: str
    chain: ArkhamChain
    event_type: ArkhamEventType
    direction: ArkhamFlowDirection
    asset: str
    amount_usd: float
    source_entity: str
    destination_entity: str
    observed_at: datetime

    def __post_init__(self) -> None:

        if not isinstance(self.event_id, str):
            raise TypeError(
                "event_id must be string"
            )

        event_id = self.event_id.strip()

        if not event_id:
            raise ValueError(
                "event_id required"
            )

        object.__setattr__(
            self,
            "event_id",
            event_id,
        )

        if not isinstance(
            self.chain,
            ArkhamChain,
        ):
            raise TypeError(
                "chain must be ArkhamChain"
            )

        if not isinstance(
            self.event_type,
            ArkhamEventType,
        ):
            raise TypeError(
                "event_type must be ArkhamEventType"
            )

        if not isinstance(
            self.direction,
            ArkhamFlowDirection,
        ):
            raise TypeError(
                "direction must be ArkhamFlowDirection"
            )

        asset = self.asset.strip().upper()

        if not asset:
            raise ValueError(
                "asset required"
            )

        asset_aliases = {
            "TETHER USD": "USDT",
            "USD COIN": "USDC",
            "ETHEREUM": "ETH",
            "BITCOIN": "BTC",
        }

        asset = asset_aliases.get(
            asset,
            asset,
        )

        object.__setattr__(
            self,
            "asset",
            asset,
        )

        if self.amount_usd <= 0:
            raise ValueError(
                "amount_usd must be positive"
            )

        for field in (
            "source_entity",
            "destination_entity",
        ):
            value = getattr(
                self,
                field,
            ).strip()

            if not value:
                raise ValueError(
                    f"{field} required"
                )

            object.__setattr__(
                self,
                field,
                value,
            )

        if not isinstance(
            self.observed_at,
            datetime,
        ):
            raise TypeError(
                "observed_at must be datetime"
            )

        if (
            self.observed_at.tzinfo is None
        ):
            raise ValueError(
                "observed_at must be timezone aware"
            )

        object.__setattr__(
            self,
            "observed_at",
            self.observed_at.astimezone(
                timezone.utc
            ),
        )


__all__ = [
    "ArkhamWhaleEvent",
]
