import unittest
from datetime import datetime, timezone

from app.intelligence.adapters import LegacyIntelligenceAdapter
from app.intelligence.contracts import (
    Direction,
    ExpertOpinion,
    MarketState,
    TrendState,
)
from app.intelligence.market_state import MarketStateEngine
from app.intelligence.shadow import ShadowIntelligenceEngine


FIXED_TIME = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


def opinion(
    name,
    direction=Direction.NEUTRAL,
    state="UNKNOWN",
    score=80,
    confidence=90,
    quality=90,
    reasons=(),
):
    return ExpertOpinion(
        expert_name=name,
        direction=direction,
        state=state,
        score=score,
        confidence=confidence,
        quality=quality,
        reasons=reasons,
        timestamp=FIXED_TIME,
    )


class ShadowIntelligenceEngineTests(unittest.TestCase):
    def setUp(self):
        self.shadow = ShadowIntelligenceEngine()

    def test_add_valid_opinion(self):
        value = opinion("trend")

        self.shadow.add_opinion(value)

        self.assertEqual(self.shadow.get_opinions(), (value,))

    def test_multiple_opinions_preserve_registration_order(self):
        first = opinion("trend", Direction.BULLISH, "TREND")
        second = opinion("funding", Direction.NEUTRAL, "CORRECTION")

        self.shadow.add_opinion(first)
        self.shadow.add_opinion(second)

        self.assertEqual(self.shadow.get_opinions(), (first, second))

    def test_empty_state_is_delegated_to_market_state_engine(self):
        result = self.shadow.evaluate(timestamp=FIXED_TIME)

        self.assertIsInstance(result, MarketState)
        self.assertEqual(result.direction, Direction.NEUTRAL)
        self.assertEqual(result.trend, TrendState.UNKNOWN)
        self.assertTrue(any("No expert opinions" in item for item in result.warnings))

    def test_duplicate_expert_is_rejected_without_replacing_original(self):
        first = opinion("trend", Direction.BULLISH, "TREND")
        duplicate = opinion("trend", Direction.BEARISH, "REVERSAL")
        self.shadow.add_opinion(first)

        with self.assertRaisesRegex(ValueError, "duplicate expert opinion"):
            self.shadow.add_opinion(duplicate)

        self.assertEqual(self.shadow.get_opinions(), (first,))

    def test_invalid_opinion_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "ExpertOpinion"):
            self.shadow.add_opinion(object())

    def test_evaluate_returns_market_state(self):
        self.shadow.add_opinion(
            opinion("trend", Direction.BULLISH, "TREND", score=85)
        )

        result = self.shadow.evaluate(timestamp=FIXED_TIME)

        self.assertIsInstance(result, MarketState)
        self.assertEqual(result.direction, Direction.BULLISH)
        self.assertEqual(result.trend, TrendState.TREND)
        self.assertEqual(result.timestamp, FIXED_TIME)

    def test_provenance_is_preserved_in_opinions_and_market_reasons(self):
        first = opinion("trend", reasons=("Structure intact",))
        second = opinion("funding", reasons=("Funding normalized",))
        self.shadow.add_opinion(first)
        self.shadow.add_opinion(second)

        result = self.shadow.evaluate(timestamp=FIXED_TIME)

        self.assertIs(self.shadow.get_opinions()[0], first)
        self.assertIs(self.shadow.get_opinions()[1], second)
        self.assertEqual(
            result.reasons,
            ("trend: Structure intact", "funding: Funding normalized"),
        )

    def test_evaluation_does_not_mutate_expert_opinion(self):
        value = opinion(
            "trend",
            Direction.BULLISH,
            "TREND",
            reasons=("Structure intact",),
        )
        before = value.to_dict()
        self.shadow.add_opinion(value)

        self.shadow.evaluate(weights={"trend": 2.0}, timestamp=FIXED_TIME)

        self.assertEqual(value.to_dict(), before)
        self.assertIs(self.shadow.get_opinions()[0], value)

    def test_custom_market_state_engine_is_used(self):
        synthesis_engine = MarketStateEngine()
        shadow = ShadowIntelligenceEngine(synthesis_engine)

        self.assertIs(shadow.market_state_engine, synthesis_engine)

    def test_legacy_adapter_output_is_accepted_as_first_source(self):
        legacy_opinion = LegacyIntelligenceAdapter().adapt(
            {
                "direction": "BULLISH",
                "state": "TREND",
                "quality": 85,
                "probability_raw": {"bullish": 80, "bearish": 20},
                "ai_decision_raw": {
                    "overall_confidence": 75,
                    "summary": "Legacy evidence supports continuation.",
                },
            },
            timestamp=FIXED_TIME,
        )
        self.shadow.add_opinion(legacy_opinion)

        result = self.shadow.evaluate(timestamp=FIXED_TIME)

        self.assertEqual(self.shadow.get_opinions(), (legacy_opinion,))
        self.assertEqual(legacy_opinion.expert_name, "legacy_intelligence")
        self.assertIsInstance(result, MarketState)


if __name__ == "__main__":
    unittest.main()
