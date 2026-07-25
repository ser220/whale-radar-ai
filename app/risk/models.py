from dataclasses import dataclass
import math

from .enums import RiskFactor, RiskLevel


@dataclass(frozen=True)
class RiskComponent:
    factor: RiskFactor
    score: float
    level: RiskLevel
    reason_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.factor, RiskFactor):
            raise TypeError("factor must be a RiskFactor")

        if isinstance(self.score, bool) or not isinstance(
            self.score,
            (int, float),
        ):
            raise TypeError("score must be a real number")

        if not math.isfinite(self.score):
            raise ValueError("score must be finite")

        if not 0.0 <= self.score <= 100.0:
            raise ValueError("score must be within 0..100")

        if not isinstance(self.level, RiskLevel):
            raise TypeError("level must be a RiskLevel")

        if not isinstance(self.reason_code, str):
            raise TypeError("reason_code must be a string")

        object.__setattr__(self, "score", float(self.score))


@dataclass(frozen=True)
class RiskScore:
    total_score: float
    liquidity_score: float
    funding_score: float
    whale_score: float
    flow_score: float
    volatility_score: float
