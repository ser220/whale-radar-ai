"""Focused tests for PS-2 Early Bird factor availability contracts."""

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from app.intelligence.early_bird import (
    EarlyBirdFactorValue,
    FactorAvailability,
)


UTC = timezone.utc
NOW = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)


def available_value(**overrides):
    values = {
        "factor_name": "funding_divergence",
        "availability": FactorAvailability.AVAILABLE,
        "score": 72,
        "observed_at": NOW,
        "source": "unified_funding_hub",
        "quality": 90,
        "reason": "Two comparable exchanges supplied fresh funding.",
        "metadata": {"exchanges": ["binance", "okx"]},
    }
    values.update(overrides)
    return EarlyBirdFactorValue(**values)


def runtime_imports():
    path = Path("app/intelligence/early_bird/availability.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


class FactorAvailabilityTests(unittest.TestCase):
    def test_enum_values(self):
        self.assertEqual(
            [item.value for item in FactorAvailability],
            ["AVAILABLE", "MISSING", "STALE", "UNSUPPORTED", "ERROR"],
        )

    def test_available_valid_value(self):
        value = available_value()
        self.assertEqual(72.0, value.score)
        self.assertIs(FactorAvailability.AVAILABLE, value.availability)

    def test_available_requires_score(self):
        with self.assertRaisesRegex(ValueError, "requires score"):
            available_value(score=None)

    def test_available_requires_timestamp(self):
        with self.assertRaisesRegex(ValueError, "requires observed_at"):
            available_value(observed_at=None)

    def test_available_requires_source(self):
        with self.assertRaisesRegex(ValueError, "requires source"):
            available_value(source=None)

    def test_score_boundaries(self):
        self.assertEqual(0.0, available_value(score=0).score)
        self.assertEqual(100.0, available_value(score=100).score)
        for score in (-0.01, 100.01, float("nan"), float("inf")):
            with self.subTest(score=score), self.assertRaises(ValueError):
                available_value(score=score)

    def test_quality_boundaries(self):
        self.assertEqual(0.0, available_value(quality=0).quality)
        self.assertEqual(100.0, available_value(quality=100).quality)
        for quality in (-0.01, 100.01, float("nan"), float("inf")):
            with self.subTest(quality=quality), self.assertRaises(ValueError):
                available_value(quality=quality)

    def test_boolean_numerics_are_rejected(self):
        with self.assertRaises(TypeError):
            available_value(score=True)
        with self.assertRaises(TypeError):
            available_value(quality=False)

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            available_value(observed_at=datetime(2026, 7, 15, 12, 0))

    def test_timestamp_is_normalized_to_utc(self):
        offset_time = datetime(
            2026,
            7,
            15,
            15,
            0,
            tzinfo=timezone(timedelta(hours=3)),
        )
        value = available_value(observed_at=offset_time)
        self.assertEqual(NOW, value.observed_at)
        self.assertIs(UTC, value.observed_at.tzinfo)

    def test_missing_without_score(self):
        value = EarlyBirdFactorValue(
            "whale_activity",
            FactorAvailability.MISSING,
            reason="No webhook arrived in the evaluation window.",
        )
        self.assertIsNone(value.score)

    def test_stale_without_score_preserves_provenance(self):
        value = EarlyBirdFactorValue(
            "volume_expansion",
            FactorAvailability.STALE,
            observed_at=NOW,
            source="binance_spot_candles",
        )
        self.assertIsNone(value.score)
        self.assertEqual(NOW, value.observed_at)

    def test_unsupported_without_score(self):
        value = EarlyBirdFactorValue(
            "liquidity_event",
            FactorAvailability.UNSUPPORTED,
        )
        self.assertIsNone(value.score)

    def test_error_without_score(self):
        value = EarlyBirdFactorValue(
            "funding_divergence",
            FactorAvailability.ERROR,
            source="unified_funding_hub",
            reason="Provider request failed.",
        )
        self.assertIsNone(value.score)

    def test_non_available_score_is_rejected(self):
        for state in (
            FactorAvailability.MISSING,
            FactorAvailability.STALE,
            FactorAvailability.UNSUPPORTED,
            FactorAvailability.ERROR,
        ):
            with self.subTest(state=state), self.assertRaisesRegex(
                ValueError, "must not include score"
            ):
                EarlyBirdFactorValue("factor", state, score=0)

    def test_factor_name_is_required(self):
        for name in ("", "   "):
            with self.subTest(name=name), self.assertRaises(ValueError):
                available_value(factor_name=name)
        with self.assertRaises(TypeError):
            available_value(factor_name=None)

    def test_optional_text_rejects_empty_values(self):
        with self.assertRaises(ValueError):
            available_value(source="  ")
        with self.assertRaises(ValueError):
            available_value(reason="  ")

    def test_contract_and_metadata_are_deeply_frozen(self):
        metadata = {"nested": {"exchanges": ["binance", "okx"]}}
        value = available_value(metadata=metadata)
        metadata["nested"]["exchanges"].append("gate")
        self.assertEqual(
            ("binance", "okx"),
            value.metadata["nested"]["exchanges"],
        )
        with self.assertRaises(FrozenInstanceError):
            value.score = 1
        with self.assertRaises(TypeError):
            value.metadata["new"] = "value"
        with self.assertRaises(TypeError):
            value.metadata["nested"]["new"] = "value"

    def test_serialization_round_trip(self):
        original = available_value(
            metadata={
                "captured_at": NOW,
                "availability": FactorAvailability.AVAILABLE,
                "nested": [1, {"valid": True}],
            }
        )
        restored = EarlyBirdFactorValue.from_dict(original.to_dict())
        self.assertEqual(original, restored)
        self.assertEqual(NOW.isoformat(), original.metadata["captured_at"])

    def test_enum_round_trip(self):
        for state in FactorAvailability:
            original = (
                available_value()
                if state is FactorAvailability.AVAILABLE
                else EarlyBirdFactorValue("factor", state)
            )
            restored = EarlyBirdFactorValue.from_dict(original.to_dict())
            self.assertIs(state, restored.availability)

    def test_from_dict_accepts_zulu_timestamp(self):
        payload = available_value().to_dict()
        payload["observed_at"] = "2026-07-15T12:00:00Z"
        restored = EarlyBirdFactorValue.from_dict(payload)
        self.assertEqual(NOW, restored.observed_at)

    def test_from_dict_requires_mapping(self):
        with self.assertRaises(TypeError):
            EarlyBirdFactorValue.from_dict([])

    def test_no_trade_fields(self):
        names = {item.name for item in fields(EarlyBirdFactorValue)}
        forbidden = {
            "recommendation",
            "signal",
            "buy",
            "sell",
            "long",
            "short",
            "entry",
            "target",
            "stop_loss",
            "execution",
        }
        self.assertTrue(names.isdisjoint(forbidden))

    def test_no_direction_fields(self):
        names = {item.name for item in fields(EarlyBirdFactorValue)}
        self.assertNotIn("direction", names)


class DependencyBoundaryTests(unittest.TestCase):
    def test_runtime_imports_stay_within_boundary(self):
        allowed_roots = {
            "dataclasses",
            "datetime",
            "enum",
            "types",
            "typing",
            "app.intelligence.early_bird.models",
        }
        imports = runtime_imports()
        self.assertTrue(set(imports).issubset(allowed_roots), imports)

    def test_runtime_has_no_forbidden_architecture_imports(self):
        imports = tuple(name.lower() for name in runtime_imports())
        forbidden = (
            "telegram",
            "fastapi",
            "database",
            "repository",
            "pipeline",
            "provider",
            "exchange_client",
            "expert",
            "marketstateengine",
            "market_state",
            "requests",
            "urllib",
            "socket",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertFalse(
                    any(token in module_name for module_name in imports),
                    imports,
                )


if __name__ == "__main__":
    unittest.main()
