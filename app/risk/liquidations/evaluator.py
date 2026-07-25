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
class LiquidationRiskInput:
    source: str
    symbol: str
    long_liquidation_notional: float
    short_liquidation_notional: float
    total_traded_notional: float
    observed_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _required_text(self.source, "source"))
        object.__setattr__(self, "symbol", _required_text(self.symbol, "symbol"))

        long_notional = _finite_real(
            self.long_liquidation_notional,
            "long_liquidation_notional",
        )
        short_notional = _finite_real(
            self.short_liquidation_notional,
            "short_liquidation_notional",
        )
        total_traded_notional = _finite_real(
            self.total_traded_notional,
            "total_traded_notional",
        )

        if long_notional < 0.0:
            raise ValueError(
                "long_liquidation_notional must be greater than or equal to 0"
            )
        if short_notional < 0.0:
            raise ValueError(
                "short_liquidation_notional must be greater than or equal to 0"
            )
        if total_traded_notional <= 0.0:
            raise ValueError("total_traded_notional must be greater than 0")

        long_notional = 0.0 if long_notional == 0.0 else long_notional
        short_notional = 0.0 if short_notional == 0.0 else short_notional
        if long_notional + short_notional > total_traded_notional:
            raise ValueError(
                "total liquidation notional must be less than or equal to "
                "total_traded_notional"
            )

        object.__setattr__(
            self,
            "long_liquidation_notional",
            long_notional,
        )
        object.__setattr__(
            self,
            "short_liquidation_notional",
            short_notional,
        )
        object.__setattr__(
            self,
            "total_traded_notional",
            total_traded_notional,
        )
        object.__setattr__(self, "observed_at", _utc_datetime(self.observed_at))


@dataclass(frozen=True)
class LiquidationRiskPolicy:
    extreme_liquidation_percent: float
    balanced_difference_percent: float
    medium_score_threshold: float
    high_score_threshold: float
    extreme_score_threshold: float

    def __post_init__(self) -> None:
        extreme_liquidation_percent = _finite_real(
            self.extreme_liquidation_percent,
            "extreme_liquidation_percent",
        )
        balanced_difference_percent = _finite_real(
            self.balanced_difference_percent,
            "balanced_difference_percent",
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

        if not 0.0 < extreme_liquidation_percent <= 100.0:
            raise ValueError(
                "extreme_liquidation_percent must be greater than 0 "
                "and less than or equal to 100"
            )
        if not 0.0 <= balanced_difference_percent <= 100.0:
            raise ValueError(
                "balanced_difference_percent must be between 0 and 100"
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
            "extreme_liquidation_percent",
            extreme_liquidation_percent,
        )
        object.__setattr__(
            self,
            "balanced_difference_percent",
            balanced_difference_percent,
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


class LiquidationRiskEvaluator:
    def evaluate(
        self,
        value: LiquidationRiskInput,
        policy: LiquidationRiskPolicy,
    ) -> RiskComponent:
        total_liquidation_notional = (
            value.long_liquidation_notional
            + value.short_liquidation_notional
        )
        liquidation_percent = (
            total_liquidation_notional
            / value.total_traded_notional
            * 100.0
        )
        score = min(
            100.0,
            liquidation_percent
            / policy.extreme_liquidation_percent
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

        if total_liquidation_notional == 0.0:
            reason_code = "LIQUIDATIONS_NONE"
        else:
            difference_percent = (
                abs(
                    value.long_liquidation_notional
                    - value.short_liquidation_notional
                )
                / total_liquidation_notional
                * 100.0
            )
            if difference_percent <= policy.balanced_difference_percent:
                reason_code = "LIQUIDATIONS_BALANCED"
            elif (
                value.long_liquidation_notional
                > value.short_liquidation_notional
            ):
                reason_code = "LONG_LIQUIDATIONS_DOMINANT"
            else:
                reason_code = "SHORT_LIQUIDATIONS_DOMINANT"

        return RiskComponent(
            factor=RiskFactor.LIQUIDATIONS,
            score=score,
            level=level,
            reason_code=reason_code,
        )
