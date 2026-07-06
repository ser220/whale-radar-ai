from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class MarketEvent:
    source: str
    event_type: str

    asset: Optional[str] = None
    amount_usd: float = 0.0

    from_entity: Optional[str] = None
    to_entity: Optional[str] = None

    network: Optional[str] = None
    tx_hash: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    raw: Dict[str, Any] = field(default_factory=dict)

    def is_exchange_inflow(self) -> bool:
        return self.event_type == "exchange_inflow"

    def is_exchange_outflow(self) -> bool:
        return self.event_type == "exchange_outflow"

    def is_large(self, threshold: float = 10_000_000) -> bool:
        return self.amount_usd >= threshold
