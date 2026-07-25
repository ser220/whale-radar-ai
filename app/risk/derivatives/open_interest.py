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
class OpenInterestRiskInput:
    source: str
    symbol: str
    open_interest: float
    previous_open_interest: float
    observed_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _required_text(self.source, "source"))
        object.__setattr__(self, "symbol", _required_text(self.symbol, "symbol"))

        open_interest = _finite_real(self.open_interest, "open_interest")
        previous_open_interest = _finite_real(
            self.previous_open_interest,
            "previous_open_interest",
        )
        if open_interest < 0.0:
            raise ValueError("open_interest must be greater than or equal to 0")
        if previous_open_interest <= 0.0:
            raise ValueError("previous_open_interest must be greater than 0")

        object.__setattr__(self, "open_interest", open_interest)
        object.__setattr__(
            self,
            "previous_open_interest",
            previous_open_interest,
        )
        object.__setattr__(self, "observed_at", _utc_datetime(self.observed_at))


@dataclass(frozen=True)
class OpenInterestRiskPolicy:
    extreme_change_percent: float
    medium_score_threshold: float
    high_score_threshold: float
    extreme_score_threshold: float

    def __post_init__(self) -> None:
        extreme_change_percent = _finite_real(
            self.extreme_change_percent,
            "extreme_change_percent",
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

        if extreme_change_percent <= 0.0:
            raise ValueError("extreme_change_percent must be greater than 0")
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
            "extreme_change_percent",
            extreme_change_percent,
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


class OpenInterestRiskEvaluator:
    def evaluate(
        self,
        value: OpenInterestRiskInput,
        policy: OpenInterestRiskPolicy,
    ) -> RiskComponent:
        change_percent = (
            (value.open_interest - value.previous_open_interest)
            / value.previous_open_interest
            * 100.0
        )
        score = min(
            100.0,
            abs(change_percent)
            / policy.extreme_change_percent
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

        if change_percent > 0.0:
            reason_code = "OI_INCREASE"
        elif change_percent < 0.0:
            reason_code = "OI_DECREASE"
        else:
            reason_code = "OI_UNCHANGED"

        return RiskComponent(
            factor=RiskFactor.OPEN_INTEREST,
            score=score,
            level=level,
            reason_code=reason_code,
        )
