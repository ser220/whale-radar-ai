from typing import Iterable, Tuple

from app.risk.aggregation.models import (
    AggregatedRiskScore,
    RiskAggregationPolicy,
)
from app.risk.enums import RiskFactor, RiskLevel
from app.risk.models import RiskComponent


class RiskAggregator:
    def aggregate(
        self,
        components: Iterable[RiskComponent],
        policy: RiskAggregationPolicy,
    ) -> AggregatedRiskScore:
        normalized_components = tuple(components)

        if not normalized_components:
            raise ValueError(
                "At least one risk component is required for aggregation."
            )

        seen_factors = set()

        for component in normalized_components:
            if component.factor in seen_factors:
                raise ValueError(
                    f"Duplicate risk factor: {component.factor.name}."
                )

            seen_factors.add(component.factor)

        weighted_score_sum = 0.0
        active_weight_sum = 0.0

        for component in normalized_components:
            weight = policy.weights.get(component.factor)

            if weight is None:
                raise ValueError(
                    f"No aggregation weight configured for "
                    f"{component.factor.name}."
                )

            if weight == 0.0:
                continue

            weighted_score_sum += component.score * weight
            active_weight_sum += weight

        if active_weight_sum == 0.0:
            raise ValueError(
                "At least one component must have a positive active weight."
            )

        total_score = weighted_score_sum / active_weight_sum

        return AggregatedRiskScore(
            total_score=total_score,
            level=self._resolve_level(
                total_score=total_score,
                policy=policy,
            ),
            components=normalized_components,
        )

    @staticmethod
    def _resolve_level(
        total_score: float,
        policy: RiskAggregationPolicy,
    ) -> RiskLevel:
        if total_score >= policy.extreme_score_threshold:
            return RiskLevel.EXTREME

        if total_score >= policy.high_score_threshold:
            return RiskLevel.HIGH

        if total_score >= policy.medium_score_threshold:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW
