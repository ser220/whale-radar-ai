from dataclasses import dataclass

from .enums import RiskFactor, RiskLevel


@dataclass(frozen=True)
class RiskComponent:
    factor: RiskFactor
    score: float
    level: RiskLevel
    reason_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.reason_code, str):
            raise TypeError("reason_code must be a string")


@dataclass(frozen=True)
class RiskScore:
    total_score: float
    liquidity_score: float
    funding_score: float
    whale_score: float
    flow_score: float
    volatility_score: float
