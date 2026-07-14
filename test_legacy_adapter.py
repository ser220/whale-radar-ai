import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

from app.intelligence.adapters import LegacyIntelligenceAdapter
from app.intelligence.contracts import Direction, ExpertOpinion
from app.intelligence.market_state import MarketStateEngine


class LegacyIntelligenceAdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = LegacyIntelligenceAdapter()
        self.timestamp = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)

    def valid_payload(self):
        return {
            "summary": "Exchange outflow with accumulation pressure.",
            "action": "Watch BTC for continuation.",
            "probability_raw": {
                "bullish": 72,
                "bearish": 28,
                "bias": "Bullish Continuation",
            },
            "ai_decision_raw": {
                "overall_confidence": 78,
                "best_action": "Look for long continuation",
                "summary": "Bullish scenario remains primary.",
                "invalidates": ["Large exchange inflows"],
            },
            "market_regime_raw": {
                "regime": "Accumulation",
                "risk": "Medium",
                "message": "Exchange outflow pressure remains dominant.",
            },
            "meta_decision_raw": {"final": 81},
            "self_confidence_raw": {
                "score": 74,
                "reasons": ["Context is sufficiently mature."],
            },
            "pattern_confidence_raw": {"pattern": 79, "seen": 20},
            "source_consensus": "Two legacy confirmations.",
            "campaign": "Accumulation campaign detected.",
            "event_memory": "Three related events.",
        }

    def test_valid_conversion(self):
        opinion = self.adapter.adapt(self.valid_payload(), timestamp=self.timestamp)

        self.assertIsInstance(opinion, ExpertOpinion)
        self.assertEqual(opinion.expert_name, "legacy_intelligence")
        self.assertIs(opinion.direction, Direction.BULLISH)
        self.assertEqual(opinion.state, "TREND")
        self.assertEqual(opinion.score, 81.0)
        self.assertEqual(opinion.confidence, 74.0)
        self.assertEqual(opinion.quality, 100.0)
        self.assertEqual(opinion.timestamp, self.timestamp)
        self.assertIn("Legacy probability: BULLISH 72.00%, BEARISH 28.00%.", opinion.reasons)
        self.assertIn("Legacy invalidation: Large exchange inflows", opinion.warnings)
        self.assertEqual(opinion.metadata["legacy_version"], "v20")
        self.assertEqual(
            opinion.metadata["recommendation"], "Look for long continuation"
        )
        self.assertEqual(opinion.metadata["risk"], "Medium")
        self.assertEqual(opinion.metadata["generated_at"], self.timestamp.isoformat())
        self.assertIn("source_consensus", opinion.metadata["evidence_references"])
        self.assertIn(
            "app.engine.probability_engine", opinion.metadata["source_modules"]
        )

    def test_missing_fields_produce_safe_neutral_opinion(self):
        opinion = self.adapter.adapt({}, timestamp=self.timestamp)

        self.assertIs(opinion.direction, Direction.NEUTRAL)
        self.assertEqual(opinion.state, "UNKNOWN")
        self.assertEqual(opinion.score, 0.0)
        self.assertEqual(opinion.confidence, 0.0)
        self.assertEqual(opinion.quality, 0.0)
        self.assertEqual(opinion.reasons, ())
        self.assertIn(
            "Legacy direction was unavailable; NEUTRAL was used.", opinion.warnings
        )
        self.assertIn("Legacy reasoning was unavailable.", opinion.warnings)

    def test_numeric_values_are_clamped_to_contract_boundaries(self):
        payload = {
            "probability_raw": {"bullish": 140, "bearish": -20},
            "ai_decision_raw": {"overall_confidence": 125},
            "meta_decision_raw": {"final": -10},
        }
        opinion = self.adapter.adapt(payload, timestamp=self.timestamp)

        self.assertEqual(opinion.direction, Direction.BULLISH)
        self.assertEqual(opinion.score, 0.0)
        self.assertEqual(opinion.confidence, 100.0)
        self.assertTrue(
            any("clamped to the 0-100 range" in item for item in opinion.warnings)
        )

    def test_explicit_quality_and_direction_are_supported(self):
        payload = {
            "direction": "short",
            "state": "REVERSAL",
            "quality": "88.5",
            "ai_decision_raw": {"overall_confidence": "65"},
        }
        opinion = self.adapter.adapt(payload, timestamp=self.timestamp)

        self.assertIs(opinion.direction, Direction.BEARISH)
        self.assertEqual(opinion.state, "REVERSAL")
        self.assertEqual(opinion.quality, 88.5)
        self.assertEqual(opinion.metadata["quality_basis"], "legacy_output.quality")

    def test_iso_timestamp_is_normalized_to_utc(self):
        payload = {"generated_at": "2026-07-14T15:00:00+03:00"}
        opinion = self.adapter.adapt(payload)

        self.assertEqual(opinion.timestamp, self.timestamp)
        self.assertEqual(opinion.timestamp.utcoffset(), timedelta(0))
        self.assertEqual(opinion.metadata["generated_at"], self.timestamp.isoformat())

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            self.adapter.adapt(
                self.valid_payload(), timestamp=datetime(2026, 7, 14, 12, 0)
            )

    def test_output_is_deterministic_when_timestamp_is_supplied(self):
        payload = self.valid_payload()
        first = self.adapter.adapt(payload, timestamp=self.timestamp)
        second = self.adapter.adapt(payload, timestamp=self.timestamp)

        self.assertEqual(first, second)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_output_is_accepted_by_market_state_engine(self):
        opinion = self.adapter.adapt(
            self.valid_payload(), timestamp=self.timestamp
        )

        market_state = MarketStateEngine().synthesize(
            [opinion], timestamp=self.timestamp
        )

        self.assertIs(market_state.direction, Direction.BULLISH)
        self.assertEqual(market_state.trend.value, "TREND")
        self.assertEqual(market_state.timestamp, self.timestamp)

    def test_adapter_does_not_mutate_input_and_output_is_immutable(self):
        payload = self.valid_payload()
        original_invalidates = list(payload["ai_decision_raw"]["invalidates"])
        opinion = self.adapter.adapt(payload, timestamp=self.timestamp)

        self.assertEqual(
            payload["ai_decision_raw"]["invalidates"], original_invalidates
        )
        with self.assertRaises(FrozenInstanceError):
            opinion.confidence = 10
        with self.assertRaises(TypeError):
            opinion.metadata["legacy_version"] = "changed"

    def test_invalid_input_type_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "must be a mapping"):
            self.adapter.adapt([], timestamp=self.timestamp)

    def test_empty_legacy_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            LegacyIntelligenceAdapter(" ")


if __name__ == "__main__":
    unittest.main()
