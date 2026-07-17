"""Deterministic tests for the Binance live smoke runner."""

from datetime import datetime, timezone
from io import StringIO
import json
import unittest

from app.intelligence.data_sources import DataSourceType, MarketSnapshot
from app.intelligence.data_sources.collectors import BinanceMarketCollector
from run_binance_market_smoke import collect_and_print_snapshot


CAPTURED_AT = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        payload = {
            "symbol": "BTCUSDT",
            "lastPrice": "120000.25",
            "volume": "35000.5",
            "priceChangePercent": "-2.75",
            "closeTime": int(CAPTURED_AT.timestamp() * 1000),
        }
        return json.dumps(payload).encode("utf-8")


class FakeOpener:
    def __init__(self):
        self.calls = []

    def __call__(self, request, timeout):
        self.calls.append((request, timeout))
        return FakeResponse()


class BinanceMarketSmokeRunnerTests(unittest.TestCase):
    def test_runner_uses_existing_collector_and_prints_snapshot_fields(self):
        opener = FakeOpener()
        collector = BinanceMarketCollector(
            timeout_seconds=2.5,
            opener=opener,
        )
        output = StringIO()

        snapshot = collect_and_print_snapshot(
            collector,
            "BTCUSDT",
            output,
        )

        self.assertIsInstance(snapshot, MarketSnapshot)
        self.assertIs(snapshot.source, DataSourceType.BINANCE)
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(
            output.getvalue(),
            "source: BINANCE\n"
            "symbol: BTCUSDT\n"
            "price: 120000.25\n"
            "volume_24h: 35000.5\n"
            "change_24h: -2.75\n"
            "captured_at: 2026-07-17T12:00:00+00:00\n",
        )


if __name__ == "__main__":
    unittest.main()
