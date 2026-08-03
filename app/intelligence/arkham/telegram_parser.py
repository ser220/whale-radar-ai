from __future__ import annotations

import re

from datetime import datetime, timezone

from .models import ArkhamWhaleEvent
from .enums import (
    ArkhamChain,
    ArkhamEventType,
    ArkhamFlowDirection,
)


class ArkhamTelegramParser:
    """
    Parses Arkham Telegram alerts.

    No decision logic.
    """

    def parse(
        self,
        text: str,
    ) -> ArkhamWhaleEvent:

        if not isinstance(text, str):
            raise TypeError(
                "text must be string"
            )

        upper = text.upper()

        if "CEX WITHDRAWAL" in upper:
            event_type = (
                ArkhamEventType.CEX_WITHDRAWAL
            )
            direction = (
                ArkhamFlowDirection.OUTFLOW
            )

        elif "CEX DEPOSIT" in upper:
            event_type = (
                ArkhamEventType.CEX_DEPOSIT
            )
            direction = (
                ArkhamFlowDirection.INFLOW
            )

        else:
            event_type = (
                ArkhamEventType.WHALE_TRANSFER
            )
            direction = (
                ArkhamFlowDirection.OUTFLOW
            )


        value_match = re.search(
            r"\(\$([\d,]+\.\d+)",
            text,
        )

        amount_usd = (
            float(
                value_match.group(1)
                .replace(",", "")
            )
            if value_match
            else 0.0
        )


        asset_match = re.search(
            r"Value:\s*[\d,.]+\s+(.+?)\s+\(\$",
            text,
        )

        asset = (
            asset_match.group(1)
            .strip()
            if asset_match
            else "UNKNOWN"
        )

        normalized_asset = asset.upper()

        if normalized_asset == "TETHER USD":
            asset = "Tether USD"

        elif normalized_asset == "USD COIN":
            asset = "USD Coin"

        elif normalized_asset in ("ETH", "BTC"):
            asset = normalized_asset


        network_match = re.search(
            r"Network:\s*(.+)",
            text,
        )

        chain = (
            network_match.group(1)
            .strip()
            if network_match
            else "OTHER"
        )


        return ArkhamWhaleEvent(
            event_id=f"telegram-{int(datetime.now().timestamp())}",
            chain=ArkhamChain.OTHER,
            event_type=event_type,
            direction=direction,
            asset=asset,
            amount_usd=amount_usd,
            source_entity="Telegram Arkham",
            destination_entity="Unknown",
            observed_at=datetime.now(
                timezone.utc
            ),
        )


__all__ = [
    "ArkhamTelegramParser",
]
