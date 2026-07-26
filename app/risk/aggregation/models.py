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

        missing_factors = set(RiskFactor) - set(normalized)

        if missing_factors:
            missing_names = ", ".join(
                factor.name
                for factor in sorted(
                    missing_factors,
                    key=lambda item: item.value,
                )
            )
            raise ValueError(
                "Missing aggregation weights for: "
                f"{missing_names}."
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

    def __post_init__(self) -> None:
        if (
            isinstance(self.total_score, bool)
            or not isinstance(self.total_score, (int, float))
        ):
            raise TypeError("total_score must be a real number.")

        if not math.isfinite(self.total_score):
            raise ValueError("total_score must be finite.")

        normalized_score = float(self.total_score)

        if not 0.0 <= normalized_score <= 100.0:
            raise ValueError(
                "total_score must be between 0 and 100."
            )

        if not isinstance(self.level, RiskLevel):
            raise TypeError("level must be RiskLevel.")

        normalized_components = tuple(self.components)

        if not normalized_components:
            raise ValueError(
                "At least one risk component is required."
            )

        for component in normalized_components:
            if not isinstance(component, RiskComponent):
                raise TypeError(
                    "All components must be RiskComponent."
                )

        seen_factors = set()

        for component in normalized_components:
            if component.factor in seen_factors:
                raise ValueError(
                    f"Duplicate risk factor: {component.factor.name}."
                )

            seen_factors.add(component.factor)

        normalized_components = tuple(
            sorted(
                normalized_components,
                key=lambda component: component.factor.value,
            )
        )

        object.__setattr__(
            self,
            "total_score",
            normalized_score,
        )
        object.__setattr__(
            self,
            "components",
            normalized_components,
        )
