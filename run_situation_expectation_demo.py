"""Run one read-only scan and print process-local Situation expectations."""

import argparse
from typing import Iterable, Optional, Tuple

from app.intelligence.early_bird.scanner import DEFAULT_ASSETS, EarlyBirdScanner
from app.intelligence.timeline import (
    SituationExpectationEngine,
    build_timelines_from_scan,
    format_situation_expectations,
)


def _asset_argument(value: str) -> Tuple[str, ...]:
    assets = tuple(item.strip() for item in value.split(",") if item.strip())
    if not assets:
        raise argparse.ArgumentTypeError("--assets requires comma-separated symbols")
    return assets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate unevaluated hypotheses from one read-only scan.",
    )
    parser.add_argument("--assets", type=_asset_argument, default=DEFAULT_ASSETS)
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--limit", type=int, default=5)
    return parser


def generate_scan_expectations(
    *,
    scanner,
    assets: Iterable[str] = DEFAULT_ASSETS,
    timeframe: str = "15m",
    limit: int = 5,
    expectation_engine: Optional[SituationExpectationEngine] = None,
):
    """Build Timeline v1 objects and generate hypotheses without evaluation."""

    if not callable(getattr(scanner, "scan", None)):
        raise TypeError("scanner must provide scan()")
    scan_result = scanner.scan(tuple(assets), timeframe=timeframe, limit=limit)
    timeline_batch = build_timelines_from_scan(scan_result)
    engine = expectation_engine or SituationExpectationEngine()
    generated = tuple(
        (result.timeline.asset, engine.generate(result.timeline))
        for result in timeline_batch.results
    )
    return scan_result, timeline_batch, generated


def main(argv: Optional[Iterable[str]] = None) -> int:
    arguments = build_parser().parse_args(argv)
    scan_result, timeline_batch, generated = generate_scan_expectations(
        scanner=EarlyBirdScanner(),
        assets=arguments.assets,
        timeframe=arguments.timeframe,
        limit=arguments.limit,
    )
    print("Market Situation Expectation Demo")
    print("Scan timestamp: {0}".format(scan_result.started_at.isoformat()))
    print("Timeline assets: {0}".format(
        ", ".join(result.timeline.asset for result in timeline_batch.results) or "None"
    ))
    total = sum(len(expectations) for _, expectations in generated)
    print("Expectations generated: {0}".format(total))
    for asset, expectations in generated:
        if expectations:
            print("")
            print(format_situation_expectations(expectations))
    without_expectations = tuple(
        asset for asset, expectations in generated if not expectations
    )
    print("")
    print("Assets without valid expectations: {0}".format(
        ", ".join(without_expectations) or "None"
    ))
    if timeline_batch.errors:
        print("Timeline construction failures: {0}".format(len(timeline_batch.errors)))
    return 0 if timeline_batch.results else 1


if __name__ == "__main__":
    raise SystemExit(main())
