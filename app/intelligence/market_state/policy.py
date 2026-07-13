"""Validated policy values for Phase 1 market-state synthesis."""

from dataclasses import dataclass
import math
from numbers import Real


def _fraction(value: Real, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _percentage(value: Real, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 100.0:
        raise ValueError(f"{field_name} must be between 0 and 100")
    return normalized


def _positive_limit(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0")
    return value


@dataclass(frozen=True)
class SynthesisPolicy:
    """Thresholds and caps used by the deterministic Phase 1 policy."""

    direction_threshold: float = 0.15
    meaningful_direction_support: float = 0.20
    state_min_support: float = 0.20
    state_win_margin: float = 0.10
    low_quality_threshold: float = 50.0
    reason_limit: int = 20
    warning_limit: int = 20

    def __post_init__(self) -> None:
        for field_name in (
            "direction_threshold",
            "meaningful_direction_support",
            "state_min_support",
            "state_win_margin",
        ):
            object.__setattr__(self, field_name, _fraction(getattr(self, field_name), field_name))
        object.__setattr__(
            self,
            "low_quality_threshold",
            _percentage(self.low_quality_threshold, "low_quality_threshold"),
        )
        object.__setattr__(self, "reason_limit", _positive_limit(self.reason_limit, "reason_limit"))
        object.__setattr__(self, "warning_limit", _positive_limit(self.warning_limit, "warning_limit"))
