"""Run one local read-only Early Bird candle scan."""

import argparse
from typing import Iterable, Optional

from app.intelligence.early_bird.scanner import (
    DEFAULT_ASSETS,
    EarlyBirdScanner,
    format_scan_result,
)


def _asset_argument(value: str):
    assets = tuple(item.strip() for item in value.split(",") if item.strip())
    if not assets:
        raise argparse.ArgumentTypeError("--assets requires comma-separated symbols")
    return assets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the experimental read-only Early Bird scanner.",
    )
    parser.add_argument(
        "--assets",
        type=_asset_argument,
        default=DEFAULT_ASSETS,
        help="Comma-separated base assets (default: approved 10-asset universe).",
    )
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--limit", type=int, default=10)
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    arguments = build_parser().parse_args(argv)
    result = EarlyBirdScanner().scan(
        arguments.assets,
        timeframe=arguments.timeframe,
        limit=arguments.limit,
    )
    print(format_scan_result(result))
    return 0 if result.items else 1


if __name__ == "__main__":
    raise SystemExit(main())
