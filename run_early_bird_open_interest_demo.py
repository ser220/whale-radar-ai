"""Run two read-only Early Bird scans with shared Open Interest history."""

import argparse
import time
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Optional, Tuple

from app.data.market import OpenInterestHistory
from app.intelligence.early_bird.scanner import (
    DEFAULT_ASSETS,
    EarlyBirdScanner,
    OpenInterestChangeFactor,
)
from app.services.unified_open_interest_hub import (
    UnifiedOpenInterestHubService,
)


def _asset_argument(value: str) -> Tuple[str, ...]:
    assets = tuple(
        item.strip()
        for item in value.split(",")
        if item.strip()
    )

    if not assets:
        raise argparse.ArgumentTypeError(
            "--assets requires comma-separated symbols"
        )

    return assets


def _interval(value: str) -> float:
    try:
        interval = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "interval must be numeric"
        ) from exc

    if interval < 0.0:
        raise argparse.ArgumentTypeError(
            "interval must not be negative"
        )

    return interval


def run_two_scan_open_interest(
    *,
    scanner: Any,
    assets: Iterable[str] = DEFAULT_ASSETS,
    timeframe: str = "15m",
    candle_count: int = 100,
    limit: int = 5,
    interval_seconds: float = 900.0,
    sleep_fn: Callable[[float], None] = time.sleep,
    clock_fn: Callable[[], datetime] = (
        lambda: datetime.now(timezone.utc)
    ),
) -> Tuple[Any, Any]:
    """Run two scans with one scanner and process-local OI history."""

    if not callable(
        getattr(
            scanner,
            "scan",
            None,
        )
    ):
        raise TypeError(
            "scanner must provide scan()"
        )

    if (
        isinstance(interval_seconds, bool)
        or not isinstance(
            interval_seconds,
            (int, float),
        )
    ):
        raise TypeError(
            "interval_seconds must be numeric"
        )

    if interval_seconds < 0:
        raise ValueError(
            "interval_seconds must not be negative"
        )

    if not callable(sleep_fn):
        raise TypeError(
            "sleep_fn must be callable"
        )

    if not callable(clock_fn):
        raise TypeError(
            "clock_fn must be callable"
        )

    normalized_assets = tuple(assets)
    first_timestamp = clock_fn()

    first_scan = scanner.scan(
        normalized_assets,
        timeframe=timeframe,
        candle_count=candle_count,
        limit=limit,
        timestamp=first_timestamp,
    )

    sleep_fn(float(interval_seconds))

    second_timestamp = clock_fn()

    second_scan = scanner.scan(
        normalized_assets,
        timeframe=timeframe,
        candle_count=candle_count,
        limit=limit,
        timestamp=second_timestamp,
    )

    return first_scan, second_scan


def _factor(scan: Any, asset: str):
    for item in scan.items:
        if item.symbol == asset:
            return item.build_result.factor_values[
                "open_interest_change"
            ]

    return None


def format_open_interest_comparison(
    first_scan: Any,
    second_scan: Any,
) -> str:
    lines = [
        "Early Bird Open Interest Demo",
        "First scan: {0}".format(
            first_scan.started_at.isoformat()
        ),
        "Second scan: {0}".format(
            second_scan.started_at.isoformat()
        ),
        "",
    ]

    assets = tuple(
        dict.fromkeys(
            first_scan.requested_assets
            + second_scan.requested_assets
        )
    )

    for asset in assets:
        first_factor = _factor(
            first_scan,
            asset,
        )
        second_factor = _factor(
            second_scan,
            asset,
        )

        lines.append("Asset: {0}".format(asset))

        if first_factor is None:
            lines.append(
                "First OI factor: unavailable"
            )
        else:
            lines.append(
                "First OI factor: {0}".format(
                    first_factor.availability.value
                )
            )

        if second_factor is None:
            lines.append(
                "Second OI factor: unavailable"
            )
        else:
            lines.append(
                "Second OI factor: {0}".format(
                    second_factor.availability.value
                )
            )
            lines.append(
                "Score: {0}".format(
                    second_factor.score
                )
            )
            lines.append(
                "Reason: {0}".format(
                    second_factor.reason
                )
            )

            change_percent = second_factor.metadata.get(
                "change_percent"
            )

            if change_percent is not None:
                lines.append(
                    "Change: {0}%".format(
                        change_percent
                    )
                )

        lines.append("")

    return "\n".join(lines).rstrip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run two live Early Bird scans with shared "
            "Open Interest history."
        ),
    )

    parser.add_argument(
        "--assets",
        type=_asset_argument,
        default=("BTC",),
    )
    parser.add_argument(
        "--timeframe",
        default="15m",
    )
    parser.add_argument(
        "--candle-count",
        type=int,
        default=100,
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--interval-seconds",
        type=_interval,
        default=900.0,
    )

    return parser


def main(
    argv: Optional[Iterable[str]] = None,
) -> int:
    arguments = build_parser().parse_args(argv)

    history = OpenInterestHistory()

    scanner = EarlyBirdScanner(
        open_interest_service=(
            UnifiedOpenInterestHubService(
                timeout=10.0,
            )
        ),
        open_interest_history=history,
        open_interest_calculator=(
            OpenInterestChangeFactor()
        ),
    )

    first_scan, second_scan = (
        run_two_scan_open_interest(
            scanner=scanner,
            assets=arguments.assets,
            timeframe=arguments.timeframe,
            candle_count=arguments.candle_count,
            limit=arguments.limit,
            interval_seconds=(
                arguments.interval_seconds
            ),
        )
    )

    print(
        format_open_interest_comparison(
            first_scan,
            second_scan,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
