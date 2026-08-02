from datetime import datetime, timedelta, timezone
from typing import Optional

from app.intelligence.data_sources import OpenInterestSnapshot
from app.intelligence.early_bird.availability import (
    EarlyBirdFactorValue,
    FactorAvailability,
)


FACTOR_NAME = "open_interest_change"
SOURCE_NAME = "open_interest_history"
FRESHNESS_WINDOW = timedelta(minutes=15)
MAX_SCORE_CHANGE_PERCENT = 10.0


def _normalize_asset(value: str) -> str:
    asset = str(value or "").strip().upper()

    if not asset:
        raise ValueError("asset must not be empty")

    return asset


def _utc_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(
            "{0} must be a datetime".format(field_name)
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(
            "{0} must be timezone aware".format(field_name)
        )

    return value.astimezone(timezone.utc)


def _validate_snapshot_asset(
    snapshot: OpenInterestSnapshot,
    asset: str,
) -> None:
    if snapshot.asset != asset:
        raise ValueError(
            "snapshot asset must match requested asset"
        )


def _score(change_percent: float) -> float:
    magnitude = abs(change_percent)

    return round(
        min(
            magnitude / MAX_SCORE_CHANGE_PERCENT * 100.0,
            100.0,
        ),
        6,
    )


class OpenInterestChangeFactor:
    """Compare two Open Interest snapshots and produce one factor value."""

    freshness_window = FRESHNESS_WINDOW

    def build(
        self,
        *,
        asset: str,
        previous: Optional[OpenInterestSnapshot],
        current: Optional[OpenInterestSnapshot],
        evaluated_at: datetime,
    ) -> EarlyBirdFactorValue:
        normalized_asset = _normalize_asset(asset)
        evaluated_utc = _utc_datetime(
            evaluated_at,
            "evaluated_at",
        )

        if previous is None or current is None:
            return EarlyBirdFactorValue(
                FACTOR_NAME,
                FactorAvailability.MISSING,
                reason=(
                    "Two Open Interest snapshots are required "
                    "to calculate change."
                ),
                metadata={
                    "asset": normalized_asset,
                    "has_previous": previous is not None,
                    "has_current": current is not None,
                },
            )

        if not isinstance(previous, OpenInterestSnapshot):
            raise TypeError(
                "previous must be an OpenInterestSnapshot or None"
            )

        if not isinstance(current, OpenInterestSnapshot):
            raise TypeError(
                "current must be an OpenInterestSnapshot or None"
            )

        _validate_snapshot_asset(
            previous,
            normalized_asset,
        )
        _validate_snapshot_asset(
            current,
            normalized_asset,
        )

        if current.captured_at < previous.captured_at:
            raise ValueError(
                "current snapshot must not be older "
                "than previous snapshot"
            )

        metadata = {
            "asset": normalized_asset,
            "previous_open_interest_usd": (
                previous.total_open_interest_usd
            ),
            "current_open_interest_usd": (
                current.total_open_interest_usd
            ),
            "previous_captured_at": (
                previous.captured_at.isoformat()
            ),
            "current_captured_at": (
                current.captured_at.isoformat()
            ),
        }

        age = evaluated_utc - current.captured_at

        if age > self.freshness_window:
            return EarlyBirdFactorValue(
                FACTOR_NAME,
                FactorAvailability.STALE,
                observed_at=current.captured_at,
                source=SOURCE_NAME,
                reason=(
                    "Current Open Interest snapshot is outside "
                    "the 15-minute freshness window."
                ),
                metadata=metadata,
            )

        previous_total = previous.total_open_interest_usd

        if previous_total <= 0:
            return EarlyBirdFactorValue(
                FACTOR_NAME,
                FactorAvailability.MISSING,
                observed_at=current.captured_at,
                source=SOURCE_NAME,
                reason=(
                    "Previous Open Interest must be positive "
                    "to calculate percentage change."
                ),
                metadata=metadata,
            )

        change_percent = (
            (
                current.total_open_interest_usd
                - previous_total
            )
            / previous_total
            * 100.0
        )

        if change_percent > 0:
            direction = "INCREASING"
        elif change_percent < 0:
            direction = "DECREASING"
        else:
            direction = "UNCHANGED"

        metadata.update(
            {
                "change_percent": round(
                    change_percent,
                    6,
                ),
                "direction": direction,
                "interval_seconds": (
                    current.captured_at
                    - previous.captured_at
                ).total_seconds(),
            }
        )

        return EarlyBirdFactorValue(
            FACTOR_NAME,
            FactorAvailability.AVAILABLE,
            score=_score(change_percent),
            observed_at=current.captured_at,
            source=SOURCE_NAME,
            quality=100.0,
            reason=(
                "Open Interest changed by {0:.6f}%."
                .format(change_percent)
            ),
            metadata=metadata,
        )
