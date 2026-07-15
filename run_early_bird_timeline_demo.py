"""Run one public read-only Early Bird scan and build in-memory Timelines."""

import argparse
from typing import Iterable, Optional

from app.intelligence.early_bird.scanner import DEFAULT_ASSETS, EarlyBirdScanner
from app.intelligence.timeline import (
    build_timelines_from_scan,
    format_early_bird_timeline,
)


def _asset_argument(value: str):
    assets = tuple(item.strip() for item in value.split(",") if item.strip())
    if not assets:
        raise argparse.ArgumentTypeError("--assets requires comma-separated symbols")
    return assets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build process-local Timeline v1 records from a read-only scan.",
    )
    parser.add_argument("--assets", type=_asset_argument, default=DEFAULT_ASSETS)
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--limit", type=int, default=10)
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    arguments = build_parser().parse_args(argv)
    scan_result = EarlyBirdScanner().scan(
        arguments.assets,
        timeframe=arguments.timeframe,
        limit=arguments.limit,
    )
    batch = build_timelines_from_scan(scan_result)

    print("Early Bird Timeline Demo")
    print("Scan timestamp: {0}".format(scan_result.started_at.isoformat()))
    print("Successful scan assets: {0}".format(
        ", ".join(scan_result.successful_assets) or "None"
    ))
    print("Failed scan assets: {0}".format(
        ", ".join(scan_result.failed_assets) or "None"
    ))
    print("Timelines created: {0}".format(len(batch.results)))
    print("Stage distribution: {0}".format(
        ", ".join(
            "{0}={1}".format(stage, count)
            for stage, count in batch.stage_distribution.items()
        ) or "None"
    ))
    print("Top assets: {0}".format(", ".join(batch.top_assets) or "None"))

    for result in batch.results:
        print("\n{0}".format(format_early_bird_timeline(result)))

    if scan_result.errors:
        print("\nScan failures:")
        for asset, error in scan_result.errors.items():
            print("- {0}: {1}".format(asset, error))
    if batch.errors:
        print("\nTimeline construction failures:")
        for asset, error in batch.errors.items():
            print("- {0}: {1}".format(asset, error))
    return 0 if batch.results else 1


if __name__ == "__main__":
    raise SystemExit(main())
