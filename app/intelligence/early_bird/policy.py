"""Validated deterministic scoring policy for Early Bird Phase 1."""

from dataclasses import dataclass, fields
import math
from numbers import Real
from typing import Any, Tuple


def _fraction(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{0} must be a real number".format(field_name))
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise ValueError("{0} must be between 0 and 1".format(field_name))
    return normalized


def _percentage(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{0} must be a real number".format(field_name))
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 100.0:
        raise ValueError("{0} must be between 0 and 100".format(field_name))
    return normalized


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{0} must be an integer".format(field_name))
    if value < 1:
        raise ValueError("{0} must be at least 1".format(field_name))
    return value


@dataclass(frozen=True)
class EarlyBirdPolicy:
    """All Phase 1 weights, thresholds, limits, and policy identity."""

    whale_activity_weight: float = 0.25
    open_interest_change_weight: float = 0.15
    funding_divergence_weight: float = 0.10
    volume_expansion_weight: float = 0.15
    relative_strength_weight: float = 0.15
    liquidity_event_weight: float = 0.10
    structure_event_weight: float = 0.05
    momentum_shift_weight: float = 0.05

    priority_opportunity_weight: float = 0.45
    priority_freshness_weight: float = 0.25
    priority_urgency_weight: float = 0.20
    priority_data_quality_weight: float = 0.10

    urgency_whale_weight: float = 0.50
    urgency_liquidity_weight: float = 0.30
    urgency_structure_weight: float = 0.20

    maturity_structure_weight: float = 0.30
    maturity_momentum_weight: float = 0.25
    maturity_volume_weight: float = 0.20
    maturity_open_interest_weight: float = 0.15
    maturity_age_weight: float = 0.10

    minimum_quality_threshold: float = 50.0
    minimum_completeness_threshold: float = 60.0
    stale_freshness_threshold: float = 30.0
    over_mature_threshold: float = 85.0
    material_factor_threshold: float = 35.0
    independent_factor_threshold: float = 35.0
    dominant_factor_share_threshold: float = 0.70
    minimum_independent_factors: int = 2
    reason_limit: int = 5
    warning_limit: int = 7
    maximum_results: int = 20
    policy_version: int = 1

    def __post_init__(self) -> None:
        fraction_fields = tuple(
            item.name
            for item in fields(self)
            if item.name.endswith("_weight")
        ) + ("dominant_factor_share_threshold",)
        for field_name in fraction_fields:
            object.__setattr__(
                self, field_name, _fraction(getattr(self, field_name), field_name)
            )

        for field_name in (
            "minimum_quality_threshold",
            "minimum_completeness_threshold",
            "stale_freshness_threshold",
            "over_mature_threshold",
            "material_factor_threshold",
            "independent_factor_threshold",
        ):
            object.__setattr__(
                self, field_name, _percentage(getattr(self, field_name), field_name)
            )

        for field_name in (
            "minimum_independent_factors",
            "reason_limit",
            "warning_limit",
            "maximum_results",
            "policy_version",
        ):
            object.__setattr__(
                self, field_name, _positive_int(getattr(self, field_name), field_name)
            )

        self._validate_weight_group(
            (
                "whale_activity_weight",
                "open_interest_change_weight",
                "funding_divergence_weight",
                "volume_expansion_weight",
                "relative_strength_weight",
                "liquidity_event_weight",
                "structure_event_weight",
                "momentum_shift_weight",
            ),
            "opportunity weights",
        )
        self._validate_weight_group(
            (
                "priority_opportunity_weight",
                "priority_freshness_weight",
                "priority_urgency_weight",
                "priority_data_quality_weight",
            ),
            "priority weights",
        )
        self._validate_weight_group(
            (
                "urgency_whale_weight",
                "urgency_liquidity_weight",
                "urgency_structure_weight",
            ),
            "urgency weights",
        )
        self._validate_weight_group(
            (
                "maturity_structure_weight",
                "maturity_momentum_weight",
                "maturity_volume_weight",
                "maturity_open_interest_weight",
                "maturity_age_weight",
            ),
            "maturity weights",
        )

    def _validate_weight_group(self, names: Tuple[str, ...], label: str) -> None:
        total = sum(getattr(self, name) for name in names)
        if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("{0} must sum to 1".format(label))
