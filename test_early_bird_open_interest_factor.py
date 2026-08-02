from datetime import datetime, timedelta, timezone

import pytest

from app.intelligence.data_sources import (
    DataSourceCategory,
    DataSourceType,
    OpenInterestSnapshot,
)
from app.intelligence.early_bird import FactorAvailability
from app.intelligence.early_bird.scanner import OpenInterestChangeFactor


NOW = datetime(2026, 8, 2, 0, 0, tzinfo=timezone.utc)


def snapshot(
    *,
    total,
    captured_at,
    asset="BTC",
    execution=None,
):
    return OpenInterestSnapshot(
        source_category=DataSourceCategory.DERIVATIVES,
        source=DataSourceType.COINGLASS,
        asset=asset,
        total_open_interest_usd=total,
        execution_open_interest_usd=(
            execution
            if execution is not None
            else total * 0.75
        ),
        exchange_count=4,
        largest_market="Binance",
        captured_at=captured_at,
    )


def build_factor(
    *,
    previous_total=16_000_000_000,
    current_total=16_800_000_000,
    previous_at=NOW - timedelta(minutes=15),
    current_at=NOW,
    evaluated_at=NOW,
):
    return OpenInterestChangeFactor().build(
        asset="BTC",
        previous=snapshot(
            total=previous_total,
            captured_at=previous_at,
        ),
        current=snapshot(
            total=current_total,
            captured_at=current_at,
        ),
        evaluated_at=evaluated_at,
    )


def test_positive_change_is_available() -> None:
    result = build_factor()

    assert result.factor_name == "open_interest_change"
    assert result.availability is FactorAvailability.AVAILABLE
    assert result.score == 50.0
    assert result.observed_at == NOW
    assert result.source == "open_interest_history"
    assert result.metadata["change_percent"] == 5.0
    assert result.metadata["previous_open_interest_usd"] == 16_000_000_000.0
    assert result.metadata["current_open_interest_usd"] == 16_800_000_000.0


def test_negative_change_uses_absolute_magnitude_for_score() -> None:
    result = build_factor(
        previous_total=16_000_000_000,
        current_total=15_200_000_000,
    )

    assert result.availability is FactorAvailability.AVAILABLE
    assert result.score == 50.0
    assert result.metadata["change_percent"] == -5.0
    assert result.metadata["direction"] == "DECREASING"


def test_zero_change_has_zero_score() -> None:
    result = build_factor(
        previous_total=16_000_000_000,
        current_total=16_000_000_000,
    )

    assert result.availability is FactorAvailability.AVAILABLE
    assert result.score == 0.0
    assert result.metadata["change_percent"] == 0.0
    assert result.metadata["direction"] == "UNCHANGED"


def test_ten_percent_or_more_reaches_maximum_score() -> None:
    result = build_factor(
        previous_total=10_000_000_000,
        current_total=11_000_000_000,
    )

    assert result.score == 100.0


def test_missing_previous_snapshot_returns_missing() -> None:
    current = snapshot(
        total=16_800_000_000,
        captured_at=NOW,
    )

    result = OpenInterestChangeFactor().build(
        asset="BTC",
        previous=None,
        current=current,
        evaluated_at=NOW,
    )

    assert result.availability is FactorAvailability.MISSING
    assert result.score is None


def test_missing_current_snapshot_returns_missing() -> None:
    previous = snapshot(
        total=16_000_000_000,
        captured_at=NOW - timedelta(minutes=15),
    )

    result = OpenInterestChangeFactor().build(
        asset="BTC",
        previous=previous,
        current=None,
        evaluated_at=NOW,
    )

    assert result.availability is FactorAvailability.MISSING
    assert result.score is None


def test_asset_mismatch_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="snapshot asset must match requested asset",
    ):
        OpenInterestChangeFactor().build(
            asset="BTC",
            previous=snapshot(
                asset="ETH",
                total=16_000_000_000,
                captured_at=NOW - timedelta(minutes=15),
            ),
            current=snapshot(
                total=16_800_000_000,
                captured_at=NOW,
            ),
            evaluated_at=NOW,
        )


def test_current_snapshot_older_than_previous_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="current snapshot must not be older than previous snapshot",
    ):
        build_factor(
            previous_at=NOW,
            current_at=NOW - timedelta(minutes=15),
        )


def test_stale_current_snapshot_returns_stale() -> None:
    result = build_factor(
        current_at=NOW - timedelta(minutes=16),
        previous_at=NOW - timedelta(minutes=31),
        evaluated_at=NOW,
    )

    assert result.availability is FactorAvailability.STALE
    assert result.score is None


def test_previous_total_must_be_positive_for_percentage_change() -> None:
    result = build_factor(
        previous_total=0,
        current_total=1_000_000,
    )

    assert result.availability is FactorAvailability.MISSING
    assert result.score is None
