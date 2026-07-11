from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class TradeDecision:
    """
    Final trading decision produced by Whale Radar AI.
    This object is presentation-independent and can be used
    by Telegram, Web UI, API and future clients.
    """

    asset: str

    status: str
    bias: str

    trade_readiness: float

    confidence: float

    institutional_score: float

    hypothesis_stability: float

    market_velocity: str

    eta: str

    action: str

    risk: str

    execution_window: str

    missing_confirmations: List[str] = field(default_factory=list)

    reasons: List[str] = field(default_factory=list)

    def is_action(self) -> bool:
        return self.status == "ACTION"

    def is_ready(self) -> bool:
        return self.trade_readiness >= 80

    def is_prepare(self) -> bool:
        return 60 <= self.trade_readiness < 80

    def is_watch(self) -> bool:
        return 30 <= self.trade_readiness < 60

    def is_no_trade(self) -> bool:
        return self.trade_readiness < 30

    def to_dict(self):
        return {
            "asset": self.asset,
            "status": self.status,
            "bias": self.bias,
            "trade_readiness": self.trade_readiness,
            "confidence": self.confidence,
            "institutional_score": self.institutional_score,
            "hypothesis_stability": self.hypothesis_stability,
            "market_velocity": self.market_velocity,
            "eta": self.eta,
            "action": self.action,
            "risk": self.risk,
            "execution_window": self.execution_window,
            "missing_confirmations": self.missing_confirmations,
            "reasons": self.reasons,
        }
