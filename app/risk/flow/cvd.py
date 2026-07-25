import math
from dataclasses import dataclass
from datetime import datetime, timezone
from numbers import Real

from app.risk.enums import RiskFactor, RiskLevel
from app.risk.models import RiskComponent


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _finite_real(value: Real, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a real number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{field_name} must be finite")
    return normalized


def _utc_datetime(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("observed_at must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class CVDRiskInput:
    source: str
    symbol: str
    cvd_delta: float
    total_volume: float
    observed_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _required_text(self.source, "source"))
        object.__setattr__(self, "symbol", _required_text(self.symbol, "symbol"))

        cvd_delta = _finite_real(self.cvd_delta, "cvd_delta")
        total_volume = _finite_real(self.total_volume, "total_volume")
        if total_volume <= 0.0:
            raise ValueError("total_volume must be greater than 0")
        if abs(cvd_delta) > total_volume:
            raise ValueError(
                "absolute cvd_delta must be less than or equal to total_volume"
            )

        object.__setattr__(self, "cvd_delta", cvd_delta)
        object.__setattr__(self, "total_volume", total_volume)
        object.__setattr__(self, "observed_at", _utc_datetime(self.observed_at))


@dataclass(frozen=True)
class CVDRiskPolicy:
    extreme_imbalance_percent: float
    medium_score_threshold: float
    high_score_threshold: float
    extreme_score_threshold: float

    def __post_init__(self) -> None:
        extreme_imbalance_percent = _finite_real(
            self.extreme_imbalance_percent,
            "extreme_imbalance_percent",
        )
        medium_score_threshold = _finite_real(
            self.medium_score_threshold,
            "medium_score_threshold",
        )
        high_score_threshold = _finite_real(
            self.high_score_threshold,
            "high_score_threshold",
        )
        extreme_score_threshold = _finite_real(
            self.extreme_score_threshold,
            "extreme_score_threshold",
        )

        if not 0.0 < extreme_imbalance_percent <= 100.0:
            raise ValueError(
                "extreme_imbalance_percent must be greater than 0 "
                "and less than or equal to 100"
            )
        if not (
            0.0
            <= medium_score_threshold
            < high_score_threshold
            < extreme_score_threshold
            <= 100.0
        ):
            raise ValueError(
                "score thresholds must satisfy "
                "0 <= medium < high < extreme <= 100"
            )

        object.__setattr__(
            self,
            "extreme_imbalance_percent",
            extreme_imbalance_percent,
        )
        object.__setattr__(
            self,
            "medium_score_threshold",
            medium_score_threshold,
        )
        object.__setattr__(
            self,
            "high_score_threshold",
            high_score_threshold,
        )
        object.__setattr__(
            self,
            "extreme_score_threshold",
            extreme_score_threshold,
        )


class CVDRiskEvaluator:
    def evaluate(
        self,
        value: CVDRiskInput,
        policy: CVDRiskPolicy,
    ) -> RiskComponent:
        imbalance_percent = value.cvd_delta / value.total_volume * 100.0
        score = min(
            100.0,
            abs(imbalance_percent)
            / policy.extreme_imbalance_percent
            * 100.0,
        )

        if score < policy.medium_score_threshold:
            level = RiskLevel.LOW
        elif score < policy.high_score_threshold:
            level = RiskLevel.MEDIUM
        elif score < policy.extreme_score_threshold:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.EXTREME

        if imbalance_percent > 0.0:
            reason_code = "CVD_BUY_DOMINANT"
        elif imbalance_percent < 0.0:
            reason_code = "CVD_SELL_DOMINANT"
        else:
            reason_code = "CVD_BALANCED"

        return RiskComponent(
            factor=RiskFactor.CVD,
            score=score,
            level=level,
            reason_code=reason_code,
        )
