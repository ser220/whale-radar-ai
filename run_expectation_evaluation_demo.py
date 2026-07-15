"""Run two read-only scans and evaluate process-local expectations."""

import argparse
from collections import Counter
import time
from typing import Any, Callable, Iterable, Optional, Tuple

from app.intelligence.early_bird.scanner import DEFAULT_ASSETS, EarlyBirdScanner
from app.intelligence.timeline import (
    SituationEvolutionEngine,
    SituationExpectationEngine,
    SituationExpectationEvaluator,
    build_timelines_from_scan,
    format_expectation_evaluations,
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


def run_two_scan_expectation_evaluation(
    *,
    scanner: Any,
    assets: Iterable[str] = DEFAULT_ASSETS,
    timeframe: str = "15m",
    limit: int = 5,
    interval_seconds: float = 60.0,
    sleep_fn: Callable[[float], None] = time.sleep,
    expectation_engine: Optional[SituationExpectationEngine] = None,
    evolution_engine: Optional[SituationEvolutionEngine] = None,
    evaluator: Optional[SituationExpectationEvaluator] = None,
):
    """Scan twice, preserve v1 hypotheses, then evaluate valid continuities."""

    if not callable(getattr(scanner, "scan", None)):
        raise TypeError("scanner must provide scan()")
    if isinstance(interval_seconds, bool) or not isinstance(interval_seconds, (int, float)):
        raise TypeError("interval_seconds must be numeric")
    if interval_seconds < 0:
        raise ValueError("interval_seconds must not be negative")
    if not callable(sleep_fn):
        raise TypeError("sleep_fn must be callable")

    normalized_assets = tuple(assets)
    first_scan = scanner.scan(normalized_assets, timeframe=timeframe, limit=limit)
    first_batch = build_timelines_from_scan(first_scan)
    first_timelines = {
        item.timeline.asset: item.timeline for item in first_batch.results
    }
    generator = expectation_engine or SituationExpectationEngine()
    expectations = tuple(
        expectation
        for item in first_batch.results
        for expectation in generator.generate(item.timeline)
    )

    sleep_fn(float(interval_seconds))

    second_scan = scanner.scan(normalized_assets, timeframe=timeframe, limit=limit)
    second_batch = build_timelines_from_scan(second_scan)
    evolution = (evolution_engine or SituationEvolutionEngine()).evolve(
        existing_timelines=first_timelines,
        candidate_timelines=tuple(item.timeline for item in second_batch.results),
        updated_at=second_scan.started_at,
        first_scan_at=first_scan.started_at,
    )
    evaluation_engine = evaluator or SituationExpectationEvaluator()
    evaluations = []
    for expectation in expectations:
        timeline = evolution.active_timelines.get(expectation.asset)
        if timeline is None or timeline.timeline_id != expectation.timeline_id:
            continue
        evaluations.append(
            evaluation_engine.evaluate(
                expectation,
                timeline,
                evaluated_at=second_scan.started_at,
            )
        )
    return first_scan, second_scan, evolution, expectations, tuple(evaluations)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate immutable hypotheses after two read-only scans.",
    )
    parser.add_argument("--assets", type=_asset_argument, default=DEFAULT_ASSETS)
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--interval-seconds", type=_interval, default=60.0)
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    arguments = build_parser().parse_args(argv)
    first, second, evolution, expectations, evaluations = (
        run_two_scan_expectation_evaluation(
            scanner=EarlyBirdScanner(),
            assets=arguments.assets,
            timeframe=arguments.timeframe,
            limit=arguments.limit,
            interval_seconds=arguments.interval_seconds,
        )
    )
    distribution = Counter(item.status.value for item in evaluations)
    print("Market Situation Expectation Evaluation Demo")
    print("First scan timestamp: {0}".format(first.started_at.isoformat()))
    print("Second scan timestamp: {0}".format(second.started_at.isoformat()))
    print("Expectations generated: {0}".format(len(expectations)))
    print("Expectations evaluated: {0}".format(len(evaluations)))
    print("Status distribution: {0}".format(
        ", ".join(
            "{0}={1}".format(name, distribution[name])
            for name in sorted(distribution)
        ) or "None"
    ))
    print("Active timelines: {0}".format(len(evolution.active_timelines)))
    if evaluations:
        print("")
        print(format_expectation_evaluations(evaluations))
    return 0 if evolution.decisions else 1


if __name__ == "__main__":
    raise SystemExit(main())
