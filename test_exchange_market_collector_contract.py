"""Focused tests for the PS-5 exchange market collector boundary."""

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import get_type_hints
import unittest

from app.intelligence.data_sources import (
    DataSourceCategory,
    DataSourceType,
    MarketSnapshot,
)
from app.intelligence.data_sources.collectors import (
    ExchangeMarketCollector,
    ExchangeMarketCollectorMetadata,
)


CAPTURED_AT = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


def metadata(**overrides):
    values = {
        "source": DataSourceType.BINANCE,
        "category": DataSourceCategory.EXCHANGE,
        "supported_symbols": ("BTCUSDT", "ETHUSDT"),
    }
    values.update(overrides)
    return ExchangeMarketCollectorMetadata(**values)


class ExampleExchangeMarketCollector:
    """Test double proving structural protocol compliance."""

    def __init__(self, collector_metadata):
        self._metadata = collector_metadata

    @property
    def metadata(self):
        return self._metadata

    def transform(self, response):
        return MarketSnapshot(
            source_category=self.metadata.category,
            source=self.metadata.source,
            symbol=response["symbol"],
            price=response["price"],
            volume_24h=response["volume_24h"],
            change_24h=response["change_24h"],
            captured_at=response["captured_at"],
        )


class IncompleteCollector:
    metadata = metadata()


class ExchangeMarketCollectorProtocolTests(unittest.TestCase):
    def test_structural_interface_compliance(self):
        collector = ExampleExchangeMarketCollector(metadata())
        self.assertIsInstance(collector, ExchangeMarketCollector)
        self.assertNotIsInstance(
            IncompleteCollector(), ExchangeMarketCollector
        )

    def test_transform_boundary_returns_market_snapshot(self):
        collector = ExampleExchangeMarketCollector(metadata())
        snapshot = collector.transform(
            {
                "symbol": "btcusdt",
                "price": 120000,
                "volume_24h": 4500000000,
                "change_24h": -2.5,
                "captured_at": CAPTURED_AT,
            }
        )
        self.assertIsInstance(snapshot, MarketSnapshot)
        self.assertIs(snapshot.source, DataSourceType.BINANCE)
        self.assertIs(snapshot.source_category, DataSourceCategory.EXCHANGE)

    def test_protocol_declares_market_snapshot_output(self):
        hints = get_type_hints(ExchangeMarketCollector.transform)
        self.assertIs(hints["return"], MarketSnapshot)


class ExchangeMarketCollectorMetadataTests(unittest.TestCase):
    def test_metadata_shape_is_exact(self):
        self.assertEqual(
            tuple(
                item.name
                for item in fields(ExchangeMarketCollectorMetadata)
            ),
            ("source", "category", "supported_symbols"),
        )

    def test_supported_sources_are_accepted(self):
        for source in (
            DataSourceType.BINANCE,
            DataSourceType.OKX,
            DataSourceType.GATE,
        ):
            with self.subTest(source=source):
                self.assertIs(metadata(source=source).source, source)

    def test_unsupported_sources_are_rejected(self):
        for source in (
            DataSourceType.BYBIT,
            DataSourceType.COINBASE,
            DataSourceType.COINGLASS,
            DataSourceType.TRADINGVIEW,
            DataSourceType.UNKNOWN,
        ):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    metadata(source=source)

    def test_category_must_be_exchange(self):
        for category in (
            DataSourceCategory.DERIVATIVES,
            DataSourceCategory.ANALYTICS,
            DataSourceCategory.UNKNOWN,
        ):
            with self.subTest(category=category):
                with self.assertRaises(ValueError):
                    metadata(category=category)

    def test_metadata_is_immutable_and_defensively_preserves_symbols(self):
        symbols = [" btcusdt ", "ethusdt"]
        value = metadata(supported_symbols=symbols)
        symbols.append("SOLUSDT")

        self.assertEqual(value.supported_symbols, ("BTCUSDT", "ETHUSDT"))
        with self.assertRaises(FrozenInstanceError):
            value.source = DataSourceType.OKX

    def test_invalid_symbol_declarations_are_rejected(self):
        invalid_values = (
            (),
            "BTCUSDT",
            ("BTCUSDT", " "),
            ("BTCUSDT", "btcusdt"),
        )
        for supported_symbols in invalid_values:
            with self.subTest(supported_symbols=supported_symbols):
                with self.assertRaises((TypeError, ValueError)):
                    metadata(supported_symbols=supported_symbols)


class ExchangeMarketCollectorArchitectureTests(unittest.TestCase):
    def test_collector_boundary_has_only_allowed_imports(self):
        package = Path("app/intelligence/data_sources/collectors")
        allowed_roots = {
            "collections",
            "dataclasses",
            "typing",
        }

        for path in package.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported = [alias.name for alias in node.names]
                    is_local = False
                elif isinstance(node, ast.ImportFrom):
                    imported = [node.module or ""]
                    is_local = node.level > 0
                else:
                    continue
                if is_local:
                    continue
                for module in imported:
                    self.assertTrue(
                        any(
                            module == root or module.startswith(root + ".")
                            for root in allowed_roots
                        ),
                        msg="forbidden import {0!r} in {1}".format(
                            module, path
                        ),
                    )

    def test_collector_boundary_is_isolated_from_ps4(self):
        package = Path("app/intelligence/data_sources/collectors")
        for path in package.rglob("*.py"):
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("app.intelligence.attachments", content)
            self.assertNotIn("governance", content.lower())


if __name__ == "__main__":
    unittest.main()
