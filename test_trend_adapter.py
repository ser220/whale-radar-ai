import unittest
from datetime import datetime, timezone

from app.intelligence.adapters import LegacyIntelligenceAdapter
from app.intelligence.contracts import (
    Direction,
    ExpertOpinion,
    MarketState,
    TrendState,
)
from app.intelligence.experts import TrendExpertAdapter
from app.intelligence.observations import (
    StructureBreak,
    StructureObservation,
    TrendBias,
    TrendObservation,
)
from app.intelligence.shadow import ShadowIntelligenceEngine


OBSERVED_AT = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
OUTPUT_AT = datetime(2026, 7, 14, 12, 5, tzinfo=timezone.utc)


def trend_observation(**overrides):
    values = {
        "observation_id": "trend-btc-4h-wr030",
        "asset": "BTC",
        "source": "normalized-candles",
        "timeframe": "4h",
        "quality": 90,
        "observed_at": OBSERVED_AT,
        "price_change_pct": 5,
        "higher_high": True,
        "higher_low": True,
        "lower_high": False,
        "lower_low": False,
        "trend_bias": TrendBias.BULLISH,
        "trend_strength": 80,
        "distance_from_range_pct": 2,
        "moving_average_alignment": TrendBias.BULLISH,
        "slope": 1,
    }
    values.update(overrides)
    return TrendObservation(**values)


def structure_observation(**overrides):
    values = {
        "observation_id": "structure-btc-4h-wr030",
        "asset": "BTC",
        "source": "normalized-structure",
        "timeframe": "4h",
        "quality": 90,
        "observed_at": OBSERVED_AT,
        "structure_break": StructureBreak.BULLISH_BOS,
        "higher_timeframe_bias": TrendBias.BULLISH,
        "structure_quality": 88,
        "swing_high": 110,
        "swing_low": 90,
        "range_high": 108,
        "range_low": 92,
        "current_price": 105,
    }
    values.update(overrides)
    return StructureObservation(**values)


def neutral_observations():
    trend = trend_observation(
        price_change_pct=0.2,
        higher_high=False,
        higher_low=False,
        lower_high=False,
        lower_low=False,
        trend_bias=TrendBias.NEUTRAL,
        trend_strength=25,
        distance_from_range_pct=0.2,
        moving_average_alignment=TrendBias.NEUTRAL,
        slope=0.02,
    )
    structure = structure_observation(
        structure_break=StructureBreak.NONE,
        higher_timeframe_bias=TrendBias.NEUTRAL,
        current_price=100,
        range_low=95,
        range_high=105,
    )
    return trend, structure


class TrendExpertAdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = TrendExpertAdapter()

    def adapt(self, trend=None, structure=None):
        return self.adapter.adapt(
            trend or trend_observation(),
            structure or structure_observation(),
            timestamp=OUTPUT_AT,
        )

    def test_valid_trend_opinion(self):
        result = self.adapt()

        self.assertIsInstance(result, ExpertOpinion)
        self.assertEqual(result.expert_name, "trend_expert")
        self.assertEqual(result.direction, Direction.BULLISH)
        self.assertEqual(result.state, TrendState.TREND.value)

    def test_neutral_trend(self):
        trend, structure = neutral_observations()

        result = self.adapt(trend, structure)

        self.assertEqual(result.direction, Direction.NEUTRAL)
        self.assertEqual(result.state, TrendState.RANGE.value)

    def test_missing_observation_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "TrendObservation"):
            self.adapter.adapt(None, structure_observation(), timestamp=OUTPUT_AT)
        with self.assertRaisesRegex(TypeError, "StructureObservation"):
            self.adapter.adapt(trend_observation(), None, timestamp=OUTPUT_AT)

    def test_confidence_is_normalized_to_contract_range(self):
        high = self.adapt()
        low = self.adapt(
            trend_observation(quality=0),
            structure_observation(quality=0, structure_quality=0),
        )

        for result in (high, low):
            self.assertGreaterEqual(result.confidence, 0.0)
            self.assertLessEqual(result.confidence, 100.0)
        self.assertLessEqual(low.confidence, high.confidence)

    def test_quality_uses_existing_trend_expert_formula(self):
        result = self.adapt(
            trend_observation(quality=80),
            structure_observation(quality=50),
        )

        self.assertEqual(result.quality, 68.0)

    def test_required_provenance_metadata_is_present(self):
        result = self.adapt()

        self.assertEqual(result.metadata["trend_source"], "normalized-candles")
        self.assertEqual(result.metadata["structure_source"], "normalized-structure")
        self.assertEqual(result.metadata["timeframe"], "4h")
        self.assertIn("trend_bias", result.metadata["indicators_used"])
        self.assertEqual(result.metadata["generated_at"], OUTPUT_AT.isoformat())
        self.assertEqual(result.metadata["source_expert_name"], "trend")

    def test_source_observations_and_opinion_values_are_not_mutated(self):
        trend = trend_observation()
        structure = structure_observation()
        trend_before = trend.to_dict()
        structure_before = structure.to_dict()

        result = self.adapt(trend, structure)

        self.assertEqual(trend.to_dict(), trend_before)
        self.assertEqual(structure.to_dict(), structure_before)
        self.assertEqual(result.timestamp, OUTPUT_AT)

    def test_legacy_and_trend_experts_coexist_in_shadow(self):
        legacy = LegacyIntelligenceAdapter().adapt(
            {
                "direction": "BULLISH",
                "state": "TREND",
                "quality": 80,
                "probability_raw": {"bullish": 75, "bearish": 25},
                "ai_decision_raw": {"overall_confidence": 70},
            },
            timestamp=OUTPUT_AT,
        )
        trend = self.adapt()
        shadow = ShadowIntelligenceEngine()

        shadow.add_opinion(legacy)
        shadow.add_opinion(trend)

        self.assertEqual(
            tuple(item.expert_name for item in shadow.get_opinions()),
            ("legacy_intelligence", "trend_expert"),
        )

    def test_market_state_synthesizes_multiple_experts(self):
        legacy = LegacyIntelligenceAdapter().adapt(
            {
                "direction": "BULLISH",
                "state": "TREND",
                "quality": 80,
                "probability_raw": {"bullish": 75, "bearish": 25},
                "ai_decision_raw": {
                    "overall_confidence": 70,
                    "summary": "Legacy evidence supports continuation.",
                },
            },
            timestamp=OUTPUT_AT,
        )
        trend = self.adapt()
        shadow = ShadowIntelligenceEngine()
        shadow.add_opinion(legacy)
        shadow.add_opinion(trend)

        result = shadow.evaluate(timestamp=OUTPUT_AT)

        self.assertIsInstance(result, MarketState)
        self.assertEqual(result.direction, Direction.BULLISH)
        self.assertEqual(result.trend, TrendState.TREND)

    def test_expert_provenance_is_preserved_after_synthesis(self):
        trend = self.adapt()
        shadow = ShadowIntelligenceEngine()
        shadow.add_opinion(trend)

        result = shadow.evaluate(timestamp=OUTPUT_AT)

        self.assertIs(shadow.get_opinions()[0], trend)
        self.assertTrue(
            any(reason.startswith("trend_expert: ") for reason in result.reasons)
        )
        self.assertEqual(trend.metadata["trend_source"], "normalized-candles")


if __name__ == "__main__":
    unittest.main()
