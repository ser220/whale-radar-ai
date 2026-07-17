"""Run one read-only live Binance public market smoke check."""

import argparse
import sys
from typing import Iterable, Optional, TextIO

from app.intelligence.data_sources import MarketSnapshot
from app.intelligence.data_sources.collectors import BinanceMarketCollector


def collect_and_print_snapshot(
    collector: BinanceMarketCollector,
    symbol: str,
    output: TextIO,
) -> MarketSnapshot:
    """Collect one snapshot and print its normalized public fields."""

    snapshot = collector.collect(symbol)
    print("source: {0}".format(snapshot.source.value), file=output)
    print("symbol: {0}".format(snapshot.symbol), file=output)
    print("price: {0}".format(snapshot.price), file=output)
    print("volume_24h: {0}".format(snapshot.volume_24h), file=output)
    print("change_24h: {0}".format(snapshot.change_24h), file=output)
    print("captured_at: {0}".format(snapshot.captured_at.isoformat()), file=output)
    return snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch and print one live public Binance MarketSnapshot.",
    )
    parser.add_argument(
        "--symbol",
        choices=("BTCUSDT", "ETHUSDT"),
        default="BTCUSDT",
        help="Supported Binance symbol (default: BTCUSDT).",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=10.0,
        help="Public HTTP request timeout (default: 10 seconds).",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    arguments = build_parser().parse_args(argv)
    collector = BinanceMarketCollector(
        timeout_seconds=arguments.timeout_seconds,
    )
    collect_and_print_snapshot(collector, arguments.symbol, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
