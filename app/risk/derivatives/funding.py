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
class FundingRiskInput:
    source: str
    symbol: str
    funding_rate: float
    funding_interval_hours: float
    observed_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _required_text(self.source, "source"))
        object.__setattr__(self, "symbol", _required_text(self.symbol, "symbol"))
        object.__setattr__(
            self,
            "funding_rate",
            _finite_real(self.funding_rate, "funding_rate"),
        )
        interval = _finite_real(
            self.funding_interval_hours,
            "funding_interval_hours",
        )
        if interval <= 0.0:
            raise ValueError("funding_interval_hours must be greater than 0")
        object.__setattr__(self, "funding_interval_hours", interval)
        object.__setattr__(self, "observed_at", _utc_datetime(self.observed_at))


@dataclass(frozen=True)
class FundingRiskPolicy:
    extreme_annualized_percent: float
    medium_score_threshold: float
    high_score_threshold: float
    extreme_score_threshold: float

    def __post_init__(self) -> None:
        extreme_annualized_percent = _finite_real(
            self.extreme_annualized_percent,
            "extreme_annualized_percent",
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

        if extreme_annualized_percent <= 0.0:
            raise ValueError("extreme_annualized_percent must be greater than 0")
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
            "extreme_annualized_percent",
            extreme_annualized_percent,
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


class FundingRiskEvaluator:
    def evaluate(
        self,
        value: FundingRiskInput,
        policy: FundingRiskPolicy,
    ) -> RiskComponent:
        annualized_percent = (
            abs(value.funding_rate)
            * (24.0 / value.funding_interval_hours)
            * 365.0
            * 100.0
        )
        score = min(
            100.0,
            annualized_percent
            / policy.extreme_annualized_percent
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

        if value.funding_rate > 0.0:
            reason_code = "FUNDING_POSITIVE"
        elif value.funding_rate < 0.0:
            reason_code = "FUNDING_NEGATIVE"
        else:
            reason_code = "FUNDING_NEUTRAL"

        return RiskComponent(
            factor=RiskFactor.FUNDING,
            score=score,
            level=level,
            reason_code=reason_code,
        )
