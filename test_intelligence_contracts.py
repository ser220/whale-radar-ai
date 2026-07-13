import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

from app.intelligence.contracts import (
    DecisionState,
    Direction,
    ExpertOpinion,
    ExpertRegistry,
    LifecycleState,
    MarketState,
    TrendState,
)


UTC_TIMESTAMP = datetime(2026, 7, 13, 9, 30, tzinfo=timezone.utc)


class IntelligenceContractTests(unittest.TestCase):
    def make_opinion(self, **overrides):
        values = {
            "expert_name": "Trend",
            "direction": Direction.BEARISH,
            "state": "CORRECTION",
            "score": 82,
            "confidence": 84,
            "quality": 91,
            "reasons": ["Price remains below resistance"],
            "warnings": ["Low timeframe volatility"],
            "metadata": {"timeframes": ["1h", "4h"], "nested": {"confirmed": True}},
            "timestamp": UTC_TIMESTAMP,
        }
        values.update(overrides)
        return ExpertOpinion(**values)

    def make_market_state(self, **overrides):
        values = {
            "trend": TrendState.CORRECTION,
            "direction": Direction.BEARISH,
            "strength": 82,
            "continuation_probability": 78,
            "correction_probability": 72,
            "reversal_probability": 16,
            "market_maturity": 65,
            "decision_stability": 93,
            "overall_confidence": 84,
            "reasons": ["Bearish structure remains intact"],
            "warnings": [],
            "timestamp": UTC_TIMESTAMP,
        }
        values.update(overrides)
        return MarketState(**values)

    def make_decision_state(self, **overrides):
        values = {
            "stage": LifecycleState.READY,
            "trade_readiness": 84,
            "eta": "17 min",
            "risk": "MEDIUM",
            "confidence": 81,
            "action": "WAIT_FOR_CONFIRMATION",
            "missing_confirmations": ["Structure break"],
            "timestamp": UTC_TIMESTAMP,
        }
        values.update(overrides)
        return DecisionState(**values)

    def test_enum_values_match_the_public_contract(self):
        self.assertEqual([item.value for item in Direction], ["BULLISH", "BEARISH", "NEUTRAL"])
        self.assertEqual(
            [item.value for item in TrendState],
            ["TREND", "CORRECTION", "REVERSAL", "RANGE", "UNKNOWN"],
        )
        self.assertEqual(
            [item.value for item in LifecycleState],
            ["WATCH", "PREPARE", "READY", "ACTION", "MANAGE", "EXIT"],
        )

    def test_expert_opinion_is_immutable_and_deep_freezes_metadata(self):
        reasons = ["Price remains below resistance"]
        metadata = {"timeframes": ["1h", "4h"], "nested": {"confirmed": True}}
        opinion = self.make_opinion(reasons=reasons, metadata=metadata)

        reasons.append("Late mutation")
        metadata["timeframes"].append("1d")

        with self.assertRaises(FrozenInstanceError):
            opinion.score = 1
        with self.assertRaises(TypeError):
            opinion.metadata["new"] = "value"
        with self.assertRaises(TypeError):
            opinion.metadata["nested"]["confirmed"] = False

        self.assertEqual(opinion.reasons, ("Price remains below resistance",))
        self.assertEqual(opinion.metadata["timeframes"], ("1h", "4h"))

    def test_market_and_decision_states_are_immutable(self):
        market_state = self.make_market_state(reasons=["Stable structure"])
        decision_state = self.make_decision_state(missing_confirmations=["Volume"])

        with self.assertRaises(FrozenInstanceError):
            market_state.strength = 1
        with self.assertRaises(FrozenInstanceError):
            decision_state.stage = LifecycleState.ACTION

        self.assertEqual(market_state.reasons, ("Stable structure",))
        self.assertEqual(decision_state.missing_confirmations, ("Volume",))

    def test_all_models_round_trip_without_losing_enums_or_timestamps(self):
        models = [self.make_opinion(), self.make_market_state(), self.make_decision_state()]

        for model in models:
            with self.subTest(model=type(model).__name__):
                restored = type(model).from_dict(model.to_dict())
                self.assertEqual(restored, model)
                self.assertIs(restored.timestamp.tzinfo, timezone.utc)

    def test_market_probabilities_and_decision_stage_serialize_as_public_values(self):
        market_payload = self.make_market_state().to_dict()
        decision_payload = self.make_decision_state().to_dict()

        self.assertEqual(market_payload["continuation_probability"], 78.0)
        self.assertEqual(market_payload["correction_probability"], 72.0)
        self.assertEqual(market_payload["reversal_probability"], 16.0)
        self.assertEqual(market_payload["overall_confidence"], 84.0)
        self.assertEqual(decision_payload["stage"], "READY")

    def test_aware_non_utc_timestamp_is_normalized_to_utc(self):
        source = datetime(2026, 7, 13, 11, 30, tzinfo=timezone(timedelta(hours=2)))
        opinion = self.make_opinion(timestamp=source)

        self.assertEqual(opinion.timestamp, UTC_TIMESTAMP)
        self.assertIs(opinion.timestamp.tzinfo, timezone.utc)

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            self.make_opinion(timestamp=datetime(2026, 7, 13, 9, 30))

    def test_percentage_fields_accept_boundaries(self):
        opinion = self.make_opinion(score=0, confidence=100, quality=0)
        market_state = self.make_market_state(
            strength=0,
            continuation_probability=100,
            correction_probability=0,
            reversal_probability=100,
            market_maturity=0,
            decision_stability=100,
            overall_confidence=0,
        )
        decision_state = self.make_decision_state(trade_readiness=0, confidence=100)

        self.assertEqual(opinion.confidence, 100.0)
        self.assertEqual(market_state.reversal_probability, 100.0)
        self.assertEqual(decision_state.trade_readiness, 0.0)

    def test_percentage_fields_reject_out_of_range_and_non_finite_values(self):
        invalid_values = (-0.01, 100.01, float("nan"), float("inf"), True)

        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    self.make_opinion(score=value)

        with self.assertRaises(ValueError):
            self.make_market_state(reversal_probability=101)
        with self.assertRaises(ValueError):
            self.make_decision_state(trade_readiness=-1)

    def test_from_dict_accepts_zulu_timestamp(self):
        payload = self.make_decision_state().to_dict()
        payload["timestamp"] = "2026-07-13T09:30:00Z"

        restored = DecisionState.from_dict(payload)

        self.assertEqual(restored.timestamp, UTC_TIMESTAMP)


class _FakeExpert:
    def __init__(self, expert_name):
        self.expert_name = expert_name


class ExpertRegistryTests(unittest.TestCase):
    def test_register_get_get_all_and_contains(self):
        registry = ExpertRegistry()
        trend = _FakeExpert("Trend")
        flow = _FakeExpert("Flow")

        registry.register(trend)
        registry.register(flow)

        self.assertTrue(registry.contains("Trend"))
        self.assertIs(registry.get("Trend"), trend)
        self.assertEqual(registry.get_all(), (trend, flow))

    def test_duplicate_requires_explicit_replace(self):
        registry = ExpertRegistry()
        first = _FakeExpert("Trend")
        replacement = _FakeExpert("Trend")
        registry.register(first)

        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.register(replacement)

        registry.register(replacement, replace=True)
        self.assertIs(registry.get("Trend"), replacement)

    def test_replace_preserves_deterministic_registration_order(self):
        registry = ExpertRegistry()
        trend = _FakeExpert("Trend")
        flow = _FakeExpert("Flow")
        replacement = _FakeExpert("Trend")
        registry.register(trend)
        registry.register(flow)

        registry.register(replacement, replace=True)

        self.assertEqual(registry.get_all(), (replacement, flow))

    def test_expert_name_is_required(self):
        registry = ExpertRegistry()

        with self.assertRaises((TypeError, ValueError)):
            registry.register(object())


if __name__ == "__main__":
    unittest.main()
