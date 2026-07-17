"""Focused tests for the live Binance public market adapter."""

from datetime import datetime, timezone
import inspect
import json
import math
import socket
import unittest
from urllib.error import URLError

from app.intelligence.data_sources import (
    DataSourceCategory,
    DataSourceType,
    MarketSnapshot,
)
from app.intelligence.data_sources.collectors import (
    BinanceMarketCollector,
    BinanceMarketCollectorResponseError,
    BinanceMarketCollectorTimeoutError,
    BinanceMarketCollectorTransportError,
    ExchangeMarketCollector,
)


CAPTURED_AT = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
CLOSE_TIME = int(CAPTURED_AT.timestamp() * 1000)


def binance_payload(**overrides):
    value = {
        "symbol": "BTCUSDT",
        "lastPrice": "120000.25",
        "volume": "35000.5",
        "priceChangePercent": "-2.75",
        "closeTime": CLOSE_TIME,
        "ignoredBinanceField": "preserved outside normalized boundary",
    }
    value.update(overrides)
    return value


class FakeResponse:
    def __init__(self, body, status=200):
        self._body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self._body


class RecordingOpener:
    def __init__(self, payload=None, raw_body=None, error=None, status=200):
        self.payload = binance_payload() if payload is None else payload
        self.raw_body = raw_body
        self.error = error
        self.status = status
        self.calls = []

    def __call__(self, request, timeout):
        self.calls.append((request, timeout))
        if self.error is not None:
            raise self.error
        body = self.raw_body
        if body is None:
            body = json.dumps(self.payload).encode("utf-8")
        return FakeResponse(body, status=self.status)


class BinanceMarketCollectorTests(unittest.TestCase):
    def test_collector_complies_with_exchange_protocol(self):
        collector = BinanceMarketCollector(opener=RecordingOpener())
        self.assertIsInstance(collector, ExchangeMarketCollector)
        self.assertIs(collector.metadata.source, DataSourceType.BINANCE)
        self.assertIs(
            collector.metadata.category, DataSourceCategory.EXCHANGE
        )
        self.assertEqual(
            collector.metadata.supported_symbols,
            ("BTCUSDT", "ETHUSDT"),
        )

    def test_successful_response_transformation(self):
        collector = BinanceMarketCollector(opener=RecordingOpener())
        snapshot = collector.transform(binance_payload())

        self.assertIsInstance(snapshot, MarketSnapshot)
        self.assertIs(snapshot.source, DataSourceType.BINANCE)
        self.assertIs(snapshot.source_category, DataSourceCategory.EXCHANGE)
        self.assertEqual(snapshot.symbol, "BTCUSDT")
        self.assertEqual(snapshot.price, 120000.25)
        self.assertEqual(snapshot.volume_24h, 35000.5)
        self.assertEqual(snapshot.change_24h, -2.75)
        self.assertEqual(snapshot.captured_at, CAPTURED_AT)
        self.assertIs(snapshot.captured_at.tzinfo, timezone.utc)

    def test_transformation_is_deterministic(self):
        collector = BinanceMarketCollector(opener=RecordingOpener())
        first = collector.transform(binance_payload())
        reversed_payload = dict(
            reversed(tuple(binance_payload().items()))
        )
        second = collector.transform(reversed_payload)
        self.assertEqual(first, second)
        self.assertEqual(first.canonical_json(), second.canonical_json())

    def test_collect_uses_public_get_endpoint_and_explicit_timeout(self):
        opener = RecordingOpener()
        collector = BinanceMarketCollector(
            timeout_seconds=3.5,
            opener=opener,
        )
        snapshot = collector.collect(" btcusdt ")

        self.assertEqual(snapshot.symbol, "BTCUSDT")
        self.assertEqual(len(opener.calls), 1)
        request, timeout = opener.calls[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(
            request.full_url,
            "https://data-api.binance.vision/api/v3/ticker/24hr"
            "?symbol=BTCUSDT",
        )
        self.assertEqual(timeout, 3.5)
        headers = {key.lower(): value for key, value in request.header_items()}
        self.assertEqual(headers, {"accept": "application/json"})
        self.assertNotIn("x-mbx-apikey", headers)
        self.assertNotIn("signature", request.full_url.lower())

    def test_unsupported_symbol_is_rejected_before_networking(self):
        opener = RecordingOpener()
        collector = BinanceMarketCollector(opener=opener)
        with self.assertRaises(ValueError):
            collector.collect("SOLUSDT")
        self.assertEqual(opener.calls, [])

    def test_mismatched_response_symbol_is_rejected(self):
        opener = RecordingOpener(payload=binance_payload(symbol="ETHUSDT"))
        collector = BinanceMarketCollector(opener=opener)
        with self.assertRaises(BinanceMarketCollectorResponseError):
            collector.collect("BTCUSDT")

    def test_invalid_responses_are_rejected(self):
        invalid_responses = (
            [],
            {},
            binance_payload(symbol="SOLUSDT"),
            binance_payload(lastPrice=""),
            binance_payload(lastPrice="not-a-number"),
            binance_payload(lastPrice="0"),
            binance_payload(volume="-1"),
            binance_payload(priceChangePercent=math.inf),
            binance_payload(closeTime=True),
            binance_payload(closeTime=-1),
            binance_payload(closeTime="not-an-integer"),
        )
        collector = BinanceMarketCollector(opener=RecordingOpener())
        for response in invalid_responses:
            with self.subTest(response=response):
                with self.assertRaises(BinanceMarketCollectorResponseError):
                    collector.transform(response)

    def test_invalid_json_and_http_status_are_rejected(self):
        invalid_json = BinanceMarketCollector(
            opener=RecordingOpener(raw_body=b"not-json")
        )
        with self.assertRaises(BinanceMarketCollectorResponseError):
            invalid_json.collect("BTCUSDT")

        non_object = BinanceMarketCollector(
            opener=RecordingOpener(raw_body=b"[]")
        )
        with self.assertRaises(BinanceMarketCollectorResponseError):
            non_object.collect("BTCUSDT")

        failed_http = BinanceMarketCollector(
            opener=RecordingOpener(status=503)
        )
        with self.assertRaises(BinanceMarketCollectorTransportError):
            failed_http.collect("BTCUSDT")

    def test_timeout_handling_covers_direct_and_wrapped_timeouts(self):
        errors = (
            socket.timeout("timed out"),
            URLError(socket.timeout("timed out")),
        )
        for error in errors:
            with self.subTest(error=error):
                collector = BinanceMarketCollector(
                    timeout_seconds=1.25,
                    opener=RecordingOpener(error=error),
                )
                with self.assertRaises(BinanceMarketCollectorTimeoutError):
                    collector.collect("BTCUSDT")

    def test_invalid_timeout_and_transport_are_rejected(self):
        for invalid in (0, -1, True, math.inf):
            with self.subTest(timeout=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    BinanceMarketCollector(timeout_seconds=invalid)

        collector = BinanceMarketCollector(
            opener=RecordingOpener(error=URLError("offline"))
        )
        with self.assertRaises(BinanceMarketCollectorTransportError):
            collector.collect("BTCUSDT")

    def test_public_constructor_has_no_authentication_parameters(self):
        parameter_names = set(
            inspect.signature(BinanceMarketCollector).parameters
        )
        forbidden = {
            "api_key",
            "api_secret",
            "credentials",
            "signature",
            "token",
        }
        self.assertTrue(forbidden.isdisjoint(parameter_names))


if __name__ == "__main__":
    unittest.main()
