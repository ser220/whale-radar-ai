"""Run two read-only Early Bird scans and evolve in-memory timelines."""

import argparse
import time
from typing import Any, Callable, Iterable, Optional, Tuple

from app.intelligence.early_bird.scanner import DEFAULT_ASSETS, EarlyBirdScanner
from app.intelligence.timeline import (
    SituationEvolutionBatchResult,
    SituationEvolutionEngine,
    build_timelines_from_scan,
    format_situation_evolution_batch,
)


def _asset_argument(value: str) -> Tuple[str, ...]:
    assets = tuple(item.strip() for item in value.split(",") if item.strip())
    if not assets:
        raise argparse.ArgumentTypeError("--assets requires comma-separated symbols")
    return assets


def _interval(value: str) -> float:
    try:
        interval = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("interval must be numeric") from exc
    if interval < 0.0:
        raise argparse.ArgumentTypeError("interval must not be negative")
    return interval


def run_two_scan_evolution(
    *,
    scanner: Any,
    assets: Iterable[str] = DEFAULT_ASSETS,
    timeframe: str = "15m",
    limit: int = 5,
    interval_seconds: float = 60.0,
    sleep_fn: Callable[[float], None] = time.sleep,
    evolution_engine: Optional[SituationEvolutionEngine] = None
) -> Tuple[Any, Any, SituationEvolutionBatchResult]:
    """Run two scans in one process; dependencies are injectable for tests."""

    if not callable(getattr(scanner, "scan", None)):
        raise TypeError("scanner must provide scan()")
    if isinstance(interval_seconds, bool) or not isinstance(interval_seconds, (int, float)):
        raise TypeError("interval_seconds must be numeric")
    if interval_seconds < 0:
        raise ValueError("interval_seconds must not be negative")
    if not callable(sleep_fn):
        raise TypeError("sleep_fn must be callable")
    normalized_assets = tuple(assets)
    first_scan = scanner.scan(
        normalized_assets,
        timeframe=timeframe,
        limit=limit,
    )
    first_batch = build_timelines_from_scan(first_scan)
    active = {
        result.timeline.asset: result.timeline for result in first_batch.results
    }

    sleep_fn(float(interval_seconds))

    second_scan = scanner.scan(
        normalized_assets,
        timeframe=timeframe,
        limit=limit,
    )
    second_batch = build_timelines_from_scan(second_scan)
    engine = evolution_engine or SituationEvolutionEngine()
    evolution = engine.evolve(
        existing_timelines=active,
        candidate_timelines=tuple(
            result.timeline for result in second_batch.results
        ),
        updated_at=second_scan.started_at,
        first_scan_at=first_scan.started_at,
    )
    return first_scan, second_scan, evolution


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run two read-only scans and evolve process-local timelines.",
    )
    parser.add_argument("--assets", type=_asset_argument, default=DEFAULT_ASSETS)
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--interval-seconds", type=_interval, default=60.0)
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    arguments = build_parser().parse_args(argv)
    first_scan, second_scan, evolution = run_two_scan_evolution(
        scanner=EarlyBirdScanner(),
        assets=arguments.assets,
        timeframe=arguments.timeframe,
        limit=arguments.limit,
        interval_seconds=arguments.interval_seconds,
    )
    print("Two-Scan Early Bird Evolution Demo")
    print("First scan timestamp: {0}".format(first_scan.started_at.isoformat()))
    print("First scan assets: {0}".format(
        ", ".join(item.symbol for item in first_scan.items) or "None"
    ))
    print("Second scan timestamp: {0}".format(second_scan.started_at.isoformat()))
    print("Second scan assets: {0}".format(
        ", ".join(item.symbol for item in second_scan.items) or "None"
    ))
    print("")
    print(format_situation_evolution_batch(evolution))
    return 0 if evolution.decisions else 1


if __name__ == "__main__":
    raise SystemExit(main())
