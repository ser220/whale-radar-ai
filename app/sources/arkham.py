from typing import Optional

from app.models.event import MarketEvent
from app.sources.base import SourceAdapter


class ArkhamAdapter(SourceAdapter):
    source_name = "arkham"

    def parse(self, payload: dict) -> Optional[MarketEvent]:
        symbol = payload.get("symbol") or payload.get("asset")
        value_usd = payload.get("valueUsd") or payload.get("amount_usd")

        if not symbol or not value_usd:
            return None

        to_label = payload.get("toLabel") or payload.get("to_entity") or "Unknown Wallet"
        from_label = payload.get("fromLabel") or payload.get("from_entity") or "Unknown Wallet"

        exchange_names = ("binance", "coinbase", "okx", "kraken", "bybit", "gate")

        if any(x in str(to_label).lower() for x in exchange_names):
            event_type = "exchange_inflow"
        elif any(x in str(from_label).lower() for x in exchange_names):
            event_type = "exchange_outflow"
        else:
            event_type = "whale_transfer"

        return MarketEvent(
            source=self.source_name,
            event_type=event_type,
            asset=str(symbol).upper(),
            amount_usd=float(value_usd),
            from_entity=from_label,
            to_entity=to_label,
            network=payload.get("chain") or payload.get("network") or "Unknown",
            tx_hash=payload.get("txHash") or payload.get("tx_hash") or "",
            raw=payload,
        )
