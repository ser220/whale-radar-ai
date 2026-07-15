"""Availability-aware funding divergence from the unified funding hub."""

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
import math
from typing import Any, Dict, Optional, Tuple

from app.intelligence.early_bird.availability import (
    EarlyBirdFactorValue,
    FactorAvailability,
)


FACTOR_NAME = "funding_divergence"
SOURCE_NAME = "unified_funding_hub"
FRESHNESS_WINDOW = timedelta(minutes=15)
MINIMUM_VENUES = 2
SPREAD_FLOOR_PERCENT = 0.005
SPREAD_CEILING_PERCENT = 0.100
MIXED_SIGN_BONUS = 15.0


def _required_asset(value: Any) -> str:
    asset = str(value or "").strip().upper()
    if not asset:
        raise ValueError("asset must not be empty")
    return asset


def _utc_datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            value = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError("{0} must be an ISO datetime".format(field_name)) from exc
    if not isinstance(value, datetime):
        raise TypeError("{0} must be a datetime".format(field_name))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("{0} must be timezone-aware".format(field_name))
    return value.astimezone(timezone.utc)


def _finite_number(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _score(spread_percent: float, mixed_sign: bool) -> float:
    if spread_percent <= SPREAD_FLOOR_PERCENT:
        score = 0.0
    elif spread_percent >= SPREAD_CEILING_PERCENT:
        score = 100.0
    else:
        score = (
            (spread_percent - SPREAD_FLOOR_PERCENT)
            / (SPREAD_CEILING_PERCENT - SPREAD_FLOOR_PERCENT)
            * 100.0
        )
    if mixed_sign:
        score += MIXED_SIGN_BONUS
    return round(min(score, 100.0), 6)


def _explicitly_unsupported(result: Mapping[str, Any], asset: str) -> bool:
    if str(result.get("status") or "").strip().lower() == "unsupported":
        return True
    unsupported_assets = result.get("unsupported_assets") or ()
    if isinstance(unsupported_assets, (str, bytes)):
        unsupported_assets = (unsupported_assets,)
    try:
        return asset in {
            str(value).strip().upper() for value in unsupported_assets
        }
    except TypeError:
        return False


def _sanitized_errors(value: Any) -> Dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(exchange).strip().lower(): "provider unavailable"
        for exchange in value
        if str(exchange).strip()
    }


class FundingDivergenceFactor:
    """Convert one unified funding response into an unsigned factor value."""

    freshness_window = FRESHNESS_WINDOW

    def build(
        self,
        asset: str,
        result: Mapping[str, Any],
        *,
        evaluated_at: datetime,
    ) -> EarlyBirdFactorValue:
        normalized_asset = _required_asset(asset)
        evaluated_utc = _utc_datetime(evaluated_at, "evaluated_at")
        if not isinstance(result, Mapping):
            raise TypeError("funding result must be a mapping")

        if _explicitly_unsupported(result, normalized_asset):
            return EarlyBirdFactorValue(
                FACTOR_NAME,
                FactorAvailability.UNSUPPORTED,
                reason="The unified funding boundary marks this asset unsupported.",
                metadata={"asset": normalized_asset},
            )

        hub_timestamp = self._optional_timestamp(result.get("captured_at"))
        exchanges = result.get("exchanges") or {}
        if not isinstance(exchanges, Mapping):
            exchanges = {}
        sanitized_errors = _sanitized_errors(
            result.get("unavailable_exchanges")
        )

        valid_rows = []
        invalid_venues = []
        for exchange_key in sorted(exchanges):
            raw_row = exchanges[exchange_key]
            if not isinstance(raw_row, Mapping):
                invalid_venues.append(str(exchange_key))
                continue
            funding_percent = _finite_number(raw_row.get("funding_percent"))
            observed_at = self._row_timestamp(raw_row, hub_timestamp)
            if funding_percent is None or observed_at is None:
                invalid_venues.append(str(exchange_key))
                continue
            age_seconds = max(
                0.0,
                (evaluated_utc - observed_at).total_seconds(),
            )
            valid_rows.append(
                {
                    "exchange": str(exchange_key).strip().lower(),
                    "exchange_name": str(
                        raw_row.get("exchange_name") or exchange_key
                    ).strip(),
                    "funding_percent": funding_percent,
                    "observed_at": observed_at,
                    "age_seconds": age_seconds,
                    "fresh": age_seconds <= self.freshness_window.total_seconds(),
                }
            )

        fresh_rows = tuple(row for row in valid_rows if row["fresh"])
        stale_rows = tuple(row for row in valid_rows if not row["fresh"])
        metadata = self._metadata(
            normalized_asset,
            fresh_rows,
            stale_rows,
            invalid_venues,
            sanitized_errors,
            hub_timestamp,
        )

        if len(fresh_rows) >= MINIMUM_VENUES:
            values = tuple(row["funding_percent"] for row in fresh_rows)
            spread = max(values) - min(values)
            mixed_sign = any(value > 0 for value in values) and any(
                value < 0 for value in values
            )
            observed_at = min(row["observed_at"] for row in fresh_rows)
            quality = self._quality(
                fresh_rows=fresh_rows,
                valid_rows=tuple(valid_rows),
                invalid_count=len(invalid_venues),
                error_count=len(sanitized_errors),
            )
            available_metadata = dict(metadata)
            available_metadata.update(
                {
                    "funding_spread_percent": round(spread, 6),
                    "mixed_sign": mixed_sign,
                    "venue_count": len(fresh_rows),
                    "used_venues": [row["exchange_name"] for row in fresh_rows],
                }
            )
            return EarlyBirdFactorValue(
                FACTOR_NAME,
                FactorAvailability.AVAILABLE,
                score=_score(spread, mixed_sign),
                observed_at=observed_at,
                source=SOURCE_NAME,
                quality=quality,
                reason=(
                    "Funding divergence uses {0} fresh comparable venues."
                    .format(len(fresh_rows))
                ),
                metadata=available_metadata,
            )

        if stale_rows and len(valid_rows) >= MINIMUM_VENUES:
            return EarlyBirdFactorValue(
                FACTOR_NAME,
                FactorAvailability.STALE,
                observed_at=min(row["observed_at"] for row in valid_rows),
                source=SOURCE_NAME,
                quality=self._provenance_quality(
                    valid_count=len(valid_rows),
                    invalid_count=len(invalid_venues),
                    error_count=len(sanitized_errors),
                ),
                reason="Comparable funding exists but is outside the 15-minute window.",
                metadata=metadata,
            )

        if not valid_rows and sanitized_errors:
            return EarlyBirdFactorValue(
                FACTOR_NAME,
                FactorAvailability.ERROR,
                source=SOURCE_NAME,
                reason="All unified funding measurements failed.",
                metadata=metadata,
            )

        return EarlyBirdFactorValue(
            FACTOR_NAME,
            FactorAvailability.MISSING,
            observed_at=(
                min(row["observed_at"] for row in valid_rows)
                if valid_rows
                else hub_timestamp
            ),
            source=SOURCE_NAME,
            quality=(
                self._provenance_quality(
                    valid_count=len(valid_rows),
                    invalid_count=len(invalid_venues),
                    error_count=len(sanitized_errors),
                )
                if valid_rows
                else None
            ),
            reason="At least two fresh comparable funding venues are required.",
            metadata=metadata,
        )

    def error(
        self,
        asset: str,
        error: Exception,
        *,
        evaluated_at: datetime,
    ) -> EarlyBirdFactorValue:
        _required_asset(asset)
        _utc_datetime(evaluated_at, "evaluated_at")
        return EarlyBirdFactorValue(
            FACTOR_NAME,
            FactorAvailability.ERROR,
            source=SOURCE_NAME,
            reason="The unified funding measurement failed.",
            metadata={
                "error_type": type(error).__name__,
                "error_detail": "provider unavailable",
            },
        )

    @staticmethod
    def _optional_timestamp(value: Any) -> Optional[datetime]:
        if value is None:
            return None
        try:
            return _utc_datetime(value, "funding timestamp")
        except (TypeError, ValueError):
            return None

    def _row_timestamp(
        self,
        row: Mapping[str, Any],
        fallback: Optional[datetime],
    ) -> Optional[datetime]:
        for field_name in ("observed_at", "captured_at", "funding_time"):
            timestamp = self._optional_timestamp(row.get(field_name))
            if timestamp is not None:
                return timestamp
        return fallback

    @staticmethod
    def _quality(
        *,
        fresh_rows: Tuple[Dict[str, Any], ...],
        valid_rows: Tuple[Dict[str, Any], ...],
        invalid_count: int,
        error_count: int,
    ) -> float:
        attempted = max(len(valid_rows) + invalid_count + error_count, 1)
        coverage = len(fresh_rows) / attempted * 100.0
        timestamps = tuple(row["observed_at"] for row in fresh_rows)
        span = (max(timestamps) - min(timestamps)).total_seconds()
        coherence = max(
            0.0,
            100.0 - span / FRESHNESS_WINDOW.total_seconds() * 100.0,
        )
        # The hub guarantees percentage-point normalization, but it does not
        # expose a per-row unit marker. Keep validity confidence below 100.
        validity = len(valid_rows) / attempted * 90.0
        return round(0.40 * coverage + 0.35 * coherence + 0.25 * validity, 6)

    @staticmethod
    def _provenance_quality(
        *,
        valid_count: int,
        invalid_count: int,
        error_count: int,
    ) -> float:
        attempted = max(valid_count + invalid_count + error_count, 1)
        return round(valid_count / attempted * 90.0, 6)

    @staticmethod
    def _metadata(
        asset: str,
        fresh_rows: Tuple[Dict[str, Any], ...],
        stale_rows: Tuple[Dict[str, Any], ...],
        invalid_venues: Any,
        errors: Mapping[str, str],
        hub_timestamp: Optional[datetime],
    ) -> Dict[str, Any]:
        return {
            "asset": asset,
            "funding_unit": "percentage_points",
            "freshness_window_seconds": int(FRESHNESS_WINDOW.total_seconds()),
            "hub_captured_at": (
                hub_timestamp.isoformat() if hub_timestamp is not None else None
            ),
            "fresh_venues": [row["exchange"] for row in fresh_rows],
            "stale_venues": [row["exchange"] for row in stale_rows],
            "invalid_venues": sorted(str(value) for value in invalid_venues),
            "venue_errors": dict(errors),
            "venue_values": {
                row["exchange"]: {
                    "funding_percent": row["funding_percent"],
                    "observed_at": row["observed_at"].isoformat(),
                }
                for row in fresh_rows + stale_rows
            },
        }


__all__ = [
    "FRESHNESS_WINDOW",
    "FundingDivergenceFactor",
    "SOURCE_NAME",
]
