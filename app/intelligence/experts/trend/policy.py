"""Validated immutable policy for Phase 1 Trend Expert evaluation."""

from dataclasses import dataclass
import math
from numbers import Real
from typing import Iterable, Tuple


def _percentage(value: Real, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 100.0:
        raise ValueError(f"{field_name} must be between 0 and 100")
    return normalized


def _non_negative(value: Real, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0.0:
        raise ValueError(f"{field_name} must be finite and non-negative")
    return normalized


def _positive_limit(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0")
    return value


def _versions(values: Iterable[int]) -> Tuple[int, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("supported_versions must be an iterable of integers")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise TypeError("supported_versions must be an iterable of integers") from exc
    if not normalized:
        raise ValueError("supported_versions must not be empty")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in normalized):
        raise TypeError("supported_versions must contain only integers")
    if any(value < 1 for value in normalized):
        raise ValueError("supported_versions must contain only positive versions")
    if len(set(normalized)) != len(normalized):
        raise ValueError("supported_versions must not contain duplicates")
    return normalized


@dataclass(frozen=True)
class TrendExpertPolicy:
    """Thresholds and caps for deterministic observation evaluation."""

    direction_lead_threshold: float = 15.0
    low_quality_threshold: float = 50.0
    timestamp_tolerance_seconds: float = 300.0
    reason_limit: int = 12
    warning_limit: int = 12
    supported_versions: Tuple[int, ...] = (1,)
    policy_version: str = "1.0"
    reversal_support_threshold: float = 25.0
    reversal_confidence_cap: float = 70.0
    weak_slope_threshold: float = 0.10
    weak_price_change_threshold: float = 1.0
    insufficient_structure_threshold: float = 25.0
    quality_gap_warning_threshold: float = 25.0

    def __post_init__(self) -> None:
        for field_name in (
            "direction_lead_threshold",
            "low_quality_threshold",
            "reversal_support_threshold",
            "reversal_confidence_cap",
            "insufficient_structure_threshold",
            "quality_gap_warning_threshold",
        ):
            object.__setattr__(
                self, field_name, _percentage(getattr(self, field_name), field_name)
            )
        for field_name in (
            "timestamp_tolerance_seconds",
            "weak_slope_threshold",
            "weak_price_change_threshold",
        ):
            object.__setattr__(
                self, field_name, _non_negative(getattr(self, field_name), field_name)
            )
        object.__setattr__(
            self, "reason_limit", _positive_limit(self.reason_limit, "reason_limit")
        )
        object.__setattr__(
            self, "warning_limit", _positive_limit(self.warning_limit, "warning_limit")
        )
        supported_versions = _versions(self.supported_versions)
        if supported_versions != (1,):
            raise ValueError("Phase 1 TrendExpert supports only observation version 1")
        object.__setattr__(self, "supported_versions", supported_versions)
        if not isinstance(self.policy_version, str):
            raise TypeError("policy_version must be a string")
        if not self.policy_version.strip():
            raise ValueError("policy_version must not be empty")
        object.__setattr__(self, "policy_version", self.policy_version.strip())
