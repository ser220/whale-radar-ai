"""Focused tests for the PS-5 immutable data source contract boundary."""

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import unittest

from app.intelligence.data_sources import (
    DataSourceCategory,
    DataSourceType,
    DerivativesSnapshot,
    MarketSnapshot,
    NewsEventSnapshot,
    SmartMoneySnapshot,
    TechnicalSignalSnapshot,
    WhaleActivitySnapshot,
)


UTC_TIME = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


def market_snapshot(**overrides):
    values = {
        "source_category": DataSourceCategory.EXCHANGE,
        "source": DataSourceType.BINANCE,
        "symbol": "btc-usdt",
        "price": 120000,
        "volume_24h": 4500000000,
        "change_24h": -2.5,
        "captured_at": UTC_TIME,
    }
    values.update(overrides)
    return MarketSnapshot(**values)


def derivatives_snapshot(**overrides):
    values = {
        "source_category": DataSourceCategory.DERIVATIVES,
        "source": DataSourceType.COINGLASS,
        "symbol": "btc-usdt",
        "open_interest": 21000000000,
        "funding_rate": -0.0001,
        "long_short_ratio": 1.08,
        "liquidation_volume": 85000000,
        "captured_at": UTC_TIME,
    }
    values.update(overrides)
    return DerivativesSnapshot(**values)


def whale_snapshot(**overrides):
    values = {
        "source_category": DataSourceCategory.ON_CHAIN,
        "source": DataSourceType.ARKHAM,
        "asset": "eth",
        "wallet_reference": "wallet:0xabc",
        "direction": "EXCHANGE_INFLOW",
        "amount": 25000,
        "entity_label": "Example Fund",
        "captured_at": UTC_TIME,
    }
    values.update(overrides)
    return WhaleActivitySnapshot(**values)


def smart_money_snapshot(**overrides):
    values = {
        "source_category": DataSourceCategory.ON_CHAIN,
        "source": DataSourceType.NANSEN,
        "wallet_reference": "wallet:smart-money-1",
        "asset": "sol",
        "activity_type": "ACCUMULATION",
        "amount": 500000,
        "captured_at": UTC_TIME,
    }
    values.update(overrides)
    return SmartMoneySnapshot(**values)


def news_snapshot(**overrides):
    values = {
        "source_category": DataSourceCategory.NEWS,
        "source": DataSourceType.UNKNOWN,
        "event_id": "news-event-001",
        "asset": "btc",
        "category": "REGULATION",
        "impact_level": "HIGH",
        "captured_at": UTC_TIME,
    }
    values.update(overrides)
    return NewsEventSnapshot(**values)


def technical_signal_snapshot(**overrides):
    values = {
        "source_category": DataSourceCategory.ANALYTICS,
        "source": DataSourceType.TRADINGVIEW,
        "symbol": "btc-usdt",
        "timeframe": "4h",
        "signal_type": "BOS",
        "direction": "BULLISH",
        "indicator_name": "Market Structure",
        "value": 1,
        "captured_at": UTC_TIME,
    }
    values.update(overrides)
    return TechnicalSignalSnapshot(**values)


class DataSourceEnumTests(unittest.TestCase):
    def test_all_data_source_categories(self):
        self.assertEqual(
            tuple(item.value for item in DataSourceCategory),
            (
                "EXCHANGE",
                "DERIVATIVES",
                "ON_CHAIN",
                "NEWS",
                "SOCIAL",
                "ANALYTICS",
                "UNKNOWN",
            ),
        )

    def test_all_data_source_types(self):
        self.assertEqual(
            tuple(item.value for item in DataSourceType),
            (
                "BINANCE",
                "OKX",
                "BYBIT",
                "GATE",
                "MEXC",
                "BITGET",
                "KUCOIN",
                "COINBASE",
                "COINGLASS",
                "ARKHAM",
                "NANSEN",
                "TRADINGVIEW",
                "UNKNOWN",
            ),
        )


class SourceCategoryValidationTests(unittest.TestCase):
    def test_all_exchange_sources_are_valid_for_market_snapshots(self):
        exchange_sources = (
            DataSourceType.BINANCE,
            DataSourceType.OKX,
            DataSourceType.BYBIT,
            DataSourceType.GATE,
            DataSourceType.MEXC,
            DataSourceType.BITGET,
            DataSourceType.KUCOIN,
            DataSourceType.COINBASE,
        )
        for source in exchange_sources:
            with self.subTest(source=source):
                self.assertIs(market_snapshot(source=source).source, source)

    def test_exchange_snapshot_rejects_non_exchange_sources(self):
        for source in (
            DataSourceType.COINGLASS,
            DataSourceType.ARKHAM,
            DataSourceType.TRADINGVIEW,
            DataSourceType.UNKNOWN,
        ):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    market_snapshot(source=source)

    def test_derivatives_snapshot_accepts_only_coinglass(self):
        self.assertIs(
            derivatives_snapshot().source, DataSourceType.COINGLASS
        )
        for source in (DataSourceType.BINANCE, DataSourceType.NANSEN):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    derivatives_snapshot(source=source)

    def test_on_chain_snapshots_accept_arkham_and_nansen(self):
        for source in (DataSourceType.ARKHAM, DataSourceType.NANSEN):
            with self.subTest(source=source):
                self.assertIs(whale_snapshot(source=source).source, source)
                self.assertIs(
                    smart_money_snapshot(source=source).source, source
                )

    def test_on_chain_snapshots_reject_other_sources(self):
        for source in (DataSourceType.BINANCE, DataSourceType.COINGLASS):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    whale_snapshot(source=source)
                with self.assertRaises(ValueError):
                    smart_money_snapshot(source=source)

    def test_news_snapshot_uses_future_unknown_source(self):
        self.assertIs(news_snapshot().source, DataSourceType.UNKNOWN)
        with self.assertRaises(ValueError):
            news_snapshot(source=DataSourceType.ARKHAM)

    def test_snapshot_rejects_wrong_category_and_unknown_enum(self):
        with self.assertRaises(ValueError):
            market_snapshot(source_category=DataSourceCategory.DERIVATIVES)
        with self.assertRaises(ValueError):
            market_snapshot(source="NOT_A_SOURCE")


class TradingViewAnalyticsContractTests(unittest.TestCase):
    def test_tradingview_requires_analytics_category(self):
        value = technical_signal_snapshot()
        self.assertIs(value.source_category, DataSourceCategory.ANALYTICS)
        self.assertIs(value.source, DataSourceType.TRADINGVIEW)

        with self.assertRaises(ValueError):
            technical_signal_snapshot(
                source_category=DataSourceCategory.EXCHANGE
            )

    def test_analytics_category_accepts_only_tradingview(self):
        for source in (
            DataSourceType.BINANCE,
            DataSourceType.COINGLASS,
            DataSourceType.UNKNOWN,
        ):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    technical_signal_snapshot(source=source)

    def test_required_analytics_text_is_validated(self):
        for field_name in (
            "symbol",
            "timeframe",
            "signal_type",
            "direction",
            "indicator_name",
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaises(ValueError):
                    technical_signal_snapshot(**{field_name: " "})

    def test_value_must_be_finite_and_not_boolean(self):
        for invalid in (True, math.nan, math.inf, -math.inf):
            with self.subTest(value=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    technical_signal_snapshot(value=invalid)

        self.assertEqual(technical_signal_snapshot(value=0).value, 0.0)
        self.assertEqual(technical_signal_snapshot(value=-2).value, -2.0)

    def test_tradingview_snapshot_is_frozen(self):
        value = technical_signal_snapshot()
        with self.assertRaises(FrozenInstanceError):
            value.direction = "BEARISH"

    def test_tradingview_serialization_round_trip_is_exact(self):
        value = technical_signal_snapshot(
            signal_type="Liquidity Sweep",
            indicator_name="Custom Pine Observation",
            value=-0.75,
        )
        restored = TechnicalSignalSnapshot.from_dict(value.to_dict())
        self.assertEqual(restored, value)
        self.assertEqual(restored.to_dict(), value.to_dict())

    def test_tradingview_canonical_json_is_stable(self):
        value = technical_signal_snapshot()
        expected = json.dumps(
            value.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        self.assertEqual(value.canonical_json(), expected)
        self.assertEqual(value.canonical_json(), value.canonical_json())

    def test_tradingview_timestamp_normalizes_to_utc(self):
        offset = timezone(timedelta(hours=-4))
        value = technical_signal_snapshot(
            captured_at=datetime(2026, 7, 17, 8, 0, tzinfo=offset)
        )
        self.assertEqual(value.captured_at, UTC_TIME)

        with self.assertRaises(ValueError):
            technical_signal_snapshot(
                captured_at=datetime(2026, 7, 17, 12, 0)
            )


class SnapshotContractTests(unittest.TestCase):
    def test_strings_are_trimmed_and_assets_are_normalized(self):
        market = market_snapshot(symbol="  eth-usdt  ")
        whale = whale_snapshot(
            asset="  btc  ", wallet_reference=" wallet:1 "
        )
        self.assertEqual(market.symbol, "ETH-USDT")
        self.assertEqual(whale.asset, "BTC")
        self.assertEqual(whale.wallet_reference, "wallet:1")

    def test_empty_required_fields_are_rejected(self):
        cases = (
            (market_snapshot, {"symbol": " "}),
            (whale_snapshot, {"wallet_reference": ""}),
            (whale_snapshot, {"direction": " "}),
            (whale_snapshot, {"entity_label": ""}),
            (smart_money_snapshot, {"activity_type": ""}),
            (news_snapshot, {"event_id": ""}),
            (news_snapshot, {"category": " "}),
            (news_snapshot, {"impact_level": ""}),
        )
        for factory, override in cases:
            with self.subTest(factory=factory.__name__, override=override):
                with self.assertRaises(ValueError):
                    factory(**override)

    def test_invalid_numeric_values_are_rejected(self):
        cases = (
            (market_snapshot, {"price": 0}),
            (market_snapshot, {"price": True}),
            (market_snapshot, {"volume_24h": -1}),
            (market_snapshot, {"change_24h": math.inf}),
            (derivatives_snapshot, {"open_interest": -1}),
            (derivatives_snapshot, {"funding_rate": math.nan}),
            (derivatives_snapshot, {"long_short_ratio": -1}),
            (derivatives_snapshot, {"liquidation_volume": -1}),
            (whale_snapshot, {"amount": 0}),
            (smart_money_snapshot, {"amount": -1}),
        )
        for factory, override in cases:
            with self.subTest(factory=factory.__name__, override=override):
                with self.assertRaises((TypeError, ValueError)):
                    factory(**override)

    def test_numeric_values_are_normalized_to_floats(self):
        market = market_snapshot(price=1, volume_24h=0, change_24h=2)
        derivatives = derivatives_snapshot(
            open_interest=0,
            funding_rate=0,
            long_short_ratio=0,
            liquidation_volume=0,
        )
        whale = whale_snapshot(amount=1)
        self.assertIsInstance(market.price, float)
        self.assertIsInstance(derivatives.open_interest, float)
        self.assertIsInstance(whale.amount, float)

    def test_timestamp_requires_awareness_and_normalizes_to_utc(self):
        with self.assertRaises(ValueError):
            market_snapshot(captured_at=datetime(2026, 7, 17, 12, 0))
        offset = timezone(timedelta(hours=2))
        value = market_snapshot(
            captured_at=datetime(2026, 7, 17, 14, 0, tzinfo=offset)
        )
        self.assertEqual(value.captured_at, UTC_TIME)

    def test_all_contracts_are_frozen(self):
        for value in (
            market_snapshot(),
            derivatives_snapshot(),
            whale_snapshot(),
            smart_money_snapshot(),
            news_snapshot(),
            technical_signal_snapshot(),
        ):
            with self.subTest(contract=type(value).__name__):
                with self.assertRaises(FrozenInstanceError):
                    value.source = DataSourceType.UNKNOWN

    def test_public_shapes_match_the_contract_boundary(self):
        expected = {
            MarketSnapshot: (
                "source_category",
                "source",
                "symbol",
                "price",
                "volume_24h",
                "change_24h",
                "captured_at",
            ),
            DerivativesSnapshot: (
                "source_category",
                "source",
                "symbol",
                "open_interest",
                "funding_rate",
                "long_short_ratio",
                "liquidation_volume",
                "captured_at",
            ),
            WhaleActivitySnapshot: (
                "source_category",
                "source",
                "asset",
                "wallet_reference",
                "direction",
                "amount",
                "entity_label",
                "captured_at",
            ),
            SmartMoneySnapshot: (
                "source_category",
                "source",
                "wallet_reference",
                "asset",
                "activity_type",
                "amount",
                "captured_at",
            ),
            NewsEventSnapshot: (
                "source_category",
                "source",
                "event_id",
                "asset",
                "category",
                "impact_level",
                "captured_at",
            ),
            TechnicalSignalSnapshot: (
                "source_category",
                "source",
                "symbol",
                "timeframe",
                "signal_type",
                "direction",
                "indicator_name",
                "value",
                "captured_at",
            ),
        }
        for contract_type, names in expected.items():
            with self.subTest(contract=contract_type.__name__):
                self.assertEqual(
                    tuple(item.name for item in fields(contract_type)), names
                )

    def test_serialization_round_trip_for_every_contract(self):
        values = (
            market_snapshot(),
            derivatives_snapshot(),
            whale_snapshot(),
            smart_money_snapshot(),
            news_snapshot(),
            technical_signal_snapshot(),
        )
        for value in values:
            with self.subTest(contract=type(value).__name__):
                restored = type(value).from_dict(value.to_dict())
                self.assertEqual(restored, value)
                self.assertEqual(restored.to_dict(), value.to_dict())

    def test_canonical_json_is_stable_for_every_contract(self):
        for value in (
            market_snapshot(),
            derivatives_snapshot(),
            whale_snapshot(),
            smart_money_snapshot(),
            news_snapshot(),
            technical_signal_snapshot(),
        ):
            with self.subTest(contract=type(value).__name__):
                self.assertEqual(value.canonical_json(), value.canonical_json())
                self.assertEqual(
                    json.loads(value.canonical_json()), value.to_dict()
                )

    def test_from_dict_accepts_enum_strings_and_iso_timestamp(self):
        payload = market_snapshot().to_dict()
        restored = MarketSnapshot.from_dict(payload)
        self.assertIs(restored.source_category, DataSourceCategory.EXCHANGE)
        self.assertIs(restored.source, DataSourceType.BINANCE)
        self.assertEqual(restored.captured_at, UTC_TIME)

    def test_from_dict_rejects_unknown_and_missing_fields(self):
        unknown = market_snapshot().to_dict()
        unknown["collector"] = "forbidden"
        with self.assertRaises(ValueError):
            MarketSnapshot.from_dict(unknown)

        missing = market_snapshot().to_dict()
        del missing["price"]
        with self.assertRaises(ValueError):
            MarketSnapshot.from_dict(missing)

    def test_contracts_expose_no_runtime_integration_fields(self):
        forbidden = {
            "api_client",
            "collector",
            "database",
            "indicator",
            "repository",
            "resolver",
            "trade_executor",
        }
        for value in (
            market_snapshot(),
            derivatives_snapshot(),
            whale_snapshot(),
            smart_money_snapshot(),
            news_snapshot(),
            technical_signal_snapshot(),
        ):
            with self.subTest(contract=type(value).__name__):
                self.assertTrue(forbidden.isdisjoint(value.to_dict()))


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_data_source_package_has_no_runtime_dependencies(self):
        package = Path("app/intelligence/data_sources")
        allowed_roots = {
            "collections",
            "dataclasses",
            "datetime",
            "enum",
            "json",
            "math",
            "numbers",
            "types",
            "typing",
        }

        for path in package.glob("*.py"):
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


if __name__ == "__main__":
    unittest.main()
