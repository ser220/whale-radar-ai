from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Mapping, Tuple

from app.risk.enums import RiskFactor, RiskLevel
from app.risk.models import RiskComponent


@dataclass(frozen=True)
class RiskAggregationPolicy:
    weights: Mapping[RiskFactor, float]

    medium_score_threshold: float
    high_score_threshold: float
    extreme_score_threshold: float

    def __post_init__(self) -> None:
        normalized = {}

        for factor, weight in self.weights.items():
            if not isinstance(factor, RiskFactor):
                raise TypeError("All weight keys must be RiskFactor.")

            if isinstance(weight, bool) or not isinstance(weight, (int, float)):
                raise TypeError(
                    f"Weight for {factor.name} must be a real number."
                )

            if not math.isfinite(weight):
                raise ValueError(
                    f"Weight for {factor.name} must be finite."
                )

            if weight < 0:
                raise ValueError(
                    f"Weight for {factor.name} cannot be negative."
                )

            normalized[factor] = float(weight)

        if not normalized:
            raise ValueError(
                "At least one aggregation weight must be configured."
            )

        if not any(weight > 0.0 for weight in normalized.values()):
            raise ValueError(
                "At least one aggregation weight must be greater than zero."
            )

        for name, value in (
            ("medium_score_threshold", self.medium_score_threshold),
            ("high_score_threshold", self.high_score_threshold),
            ("extreme_score_threshold", self.extreme_score_threshold),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be a real number.")

            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")

        medium = float(self.medium_score_threshold)
        high = float(self.high_score_threshold)
        extreme = float(self.extreme_score_threshold)

        if not (0.0 <= medium < high < extreme <= 100.0):
            raise ValueError(
                "Thresholds must satisfy "
                "0 <= medium < high < extreme <= 100."
            )

        object.__setattr__(
            self,
            "weights",
            MappingProxyType(normalized),
        )

        object.__setattr__(
            self,
            "medium_score_threshold",
            medium,
        )

        object.__setattr__(
            self,
            "high_score_threshold",
            high,
        )

        object.__setattr__(
            self,
            "extreme_score_threshold",
            extreme,
        )


@dataclass(frozen=True)
class AggregatedRiskScore:
    total_score: float
    level: RiskLevel
    components: Tuple[RiskComponent, ...]
