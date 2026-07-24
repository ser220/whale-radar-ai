from dataclasses import dataclass


@dataclass(frozen=True)
class RiskScore:
    total_score: float
    liquidity_score: float
    funding_score: float
    whale_score: float
    flow_score: float
    volatility_score: float
