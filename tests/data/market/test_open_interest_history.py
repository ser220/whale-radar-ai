from datetime import datetime, timedelta, timezone

import pytest

from app.data.market import OpenInterestHistory
from app.intelligence.data_sources import (
    DataSourceCategory,
    DataSourceType,
    OpenInterestSnapshot,
)


NOW = datetime(2026, 8, 2, 0, 0, tzinfo=timezone.utc)


def snapshot(
    *,
    asset="BTC",
    total=16_500_000_000,
    execution=12_800_000_000,
    captured_at=NOW,
):
    return OpenInterestSnapshot(
        source_category=DataSourceCategory.DERIVATIVES,
        source=DataSourceType.COINGLASS,
        asset=asset,
        total_open_interest_usd=total,
        execution_open_interest_usd=execution,
        exchange_count=4,
        largest_market="Binance",
        captured_at=captured_at,
    )


def test_history_starts_empty() -> None:
    history = OpenInterestHistory()

    assert history.assets() == ()
    assert history.snapshots("BTC") == ()
    assert history.latest("BTC") is None


def test_append_preserves_snapshot_and_asset_index() -> None:
    history = OpenInterestHistory()
    value = snapshot()

    result = history.append(value)

    assert result is value
    assert history.assets() == ("BTC",)
    assert history.snapshots("BTC") == (value,)
    assert history.latest("BTC") == value


def test_append_requires_open_interest_snapshot() -> None:
    history = OpenInterestHistory()

    with pytest.raises(
        TypeError,
        match="snapshot must be an OpenInterestSnapshot",
    ):
        history.append({})


def test_asset_lookup_normalizes_case_and_whitespace() -> None:
    history = OpenInterestHistory()
    value = snapshot(asset="BTC")
    history.append(value)

    assert history.latest(" btc ") == value
    assert history.snapshots("btc") == (value,)


def test_snapshots_are_ordered_by_captured_at() -> None:
    history = OpenInterestHistory()
    latest = snapshot(
        total=16_600_000_000,
        captured_at=NOW,
    )
    earliest = snapshot(
        total=16_400_000_000,
        captured_at=NOW - timedelta(minutes=30),
    )
    middle = snapshot(
        total=16_500_000_000,
        captured_at=NOW - timedelta(minutes=15),
    )

    history.append(latest)
    history.append(earliest)
    history.append(middle)

    assert history.snapshots("BTC") == (
        earliest,
        middle,
        latest,
    )
    assert history.latest("BTC") == latest


def test_same_asset_and_timestamp_replaces_existing_snapshot() -> None:
    history = OpenInterestHistory()
    first = snapshot(total=16_500_000_000)
    replacement = snapshot(total=16_700_000_000)

    history.append(first)
    history.append(replacement)

    assert history.snapshots("BTC") == (replacement,)
    assert history.latest("BTC") == replacement


def test_assets_are_sorted_and_unique() -> None:
    history = OpenInterestHistory()
    history.append(snapshot(asset="ETH"))
    history.append(snapshot(asset="BTC"))
    history.append(snapshot(asset="ETH"))

    assert history.assets() == ("BTC", "ETH")


def test_previous_returns_snapshot_before_reference_time() -> None:
    history = OpenInterestHistory()
    first = snapshot(
        total=16_400_000_000,
        captured_at=NOW - timedelta(minutes=30),
    )
    second = snapshot(
        total=16_500_000_000,
        captured_at=NOW - timedelta(minutes=15),
    )
    third = snapshot(
        total=16_600_000_000,
        captured_at=NOW,
    )

    for value in (first, second, third):
        history.append(value)

    assert history.previous(
        "BTC",
        before=NOW,
    ) == second


def test_previous_returns_none_when_no_earlier_snapshot_exists() -> None:
    history = OpenInterestHistory()
    history.append(snapshot())

    assert history.previous(
        "BTC",
        before=NOW,
    ) is None


def test_previous_requires_timezone_aware_datetime() -> None:
    history = OpenInterestHistory()

    with pytest.raises(
        ValueError,
        match="before must be timezone aware",
    ):
        history.previous(
            "BTC",
            before=datetime(2026, 8, 2, 0, 0),
        )


def test_at_or_before_returns_latest_snapshot_not_after_boundary() -> None:
    history = OpenInterestHistory()

    first = snapshot(
        total=16_400_000_000,
        captured_at=NOW - timedelta(minutes=30),
    )
    second = snapshot(
        total=16_500_000_000,
        captured_at=NOW - timedelta(minutes=15),
    )
    third = snapshot(
        total=16_600_000_000,
        captured_at=NOW,
    )

    for value in (first, second, third):
        history.append(value)

    assert history.at_or_before(
        "BTC",
        at=NOW - timedelta(minutes=15),
    ) == second


def test_at_or_before_returns_none_without_old_enough_snapshot() -> None:
    history = OpenInterestHistory()
    history.append(
        snapshot(
            captured_at=NOW,
        )
    )

    assert history.at_or_before(
        "BTC",
        at=NOW - timedelta(minutes=15),
    ) is None


def test_at_or_before_requires_timezone_aware_datetime() -> None:
    history = OpenInterestHistory()

    with pytest.raises(
        ValueError,
        match="at must be timezone aware",
    ):
        history.at_or_before(
            "BTC",
            at=datetime(2026, 8, 2, 0, 0),
        )
