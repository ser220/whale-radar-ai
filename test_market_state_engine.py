import unittest
from datetime import datetime, timedelta, timezone

from app.intelligence.contracts import Direction, ExpertOpinion, MarketState, TrendState
from app.intelligence.market_state import MarketStateEngine, SynthesisPolicy


FIXED_TIME = datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc)


def opinion(
    name,
    direction=Direction.NEUTRAL,
    state="UNKNOWN",
    score=80,
    confidence=90,
    quality=90,
    reasons=(),
    warnings=(),
):
    return ExpertOpinion(
        expert_name=name,
        direction=direction,
        state=state,
        score=score,
        confidence=confidence,
        quality=quality,
        reasons=reasons,
        warnings=warnings,
        timestamp=FIXED_TIME,
    )


class MarketStateEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = MarketStateEngine()

    def synthesize(self, opinions, **kwargs):
        kwargs.setdefault("timestamp", FIXED_TIME)
        return self.engine.synthesize(opinions, **kwargs)

    def test_empty_input_returns_neutral_unknown_state(self):
        result = self.synthesize([])

        self.assertEqual(result.direction, Direction.NEUTRAL)
        self.assertEqual(result.trend, TrendState.UNKNOWN)
        self.assertEqual(result.strength, 0.0)
        self.assertEqual(result.overall_confidence, 0.0)
        self.assertTrue(any("No expert opinions" in item for item in result.warnings))

    def test_one_bullish_high_quality_expert(self):
        result = self.synthesize([opinion("Trend", Direction.BULLISH, "TREND")])

        self.assertEqual(result.direction, Direction.BULLISH)
        self.assertEqual(result.trend, TrendState.TREND)
        self.assertLess(result.decision_stability, 60.0)

    def test_one_bearish_high_quality_expert(self):
        result = self.synthesize([opinion("Trend", Direction.BEARISH, "TREND")])

        self.assertEqual(result.direction, Direction.BEARISH)

    def test_balanced_direction_conflict_returns_neutral(self):
        result = self.synthesize(
            [
                opinion("Bull", Direction.BULLISH, "TREND"),
                opinion("Bear", Direction.BEARISH, "TREND"),
            ]
        )

        self.assertEqual(result.direction, Direction.NEUTRAL)
        self.assertTrue(any("direction conflict" in item for item in result.warnings))

    def test_configured_weight_overrides_conflicting_expert(self):
        values = [
            opinion("Bull", Direction.BULLISH, "TREND"),
            opinion("Bear", Direction.BEARISH, "TREND"),
        ]

        result = self.synthesize(values, weights={"Bull": 3.0, "Bear": 1.0})

        self.assertEqual(result.direction, Direction.BULLISH)

    def test_neutral_expert_does_not_create_false_direction(self):
        result = self.synthesize([opinion("Neutral", Direction.NEUTRAL, "RANGE")])

        self.assertEqual(result.direction, Direction.NEUTRAL)

    def test_all_neutral_experts_remain_neutral(self):
        result = self.synthesize(
            [opinion("One", state="RANGE"), opinion("Two", state="RANGE")]
        )

        self.assertEqual(result.direction, Direction.NEUTRAL)
        self.assertEqual(result.trend, TrendState.RANGE)

    def test_weighted_trend_state_winner(self):
        result = self.synthesize(
            [
                opinion("Trend", state=" trend "),
                opinion("Correction", state="correction"),
            ],
            weights={"Trend": 3.0, "Correction": 1.0},
        )

        self.assertEqual(result.trend, TrendState.TREND)
        self.assertGreater(result.continuation_probability, result.correction_probability)

    def test_unsupported_state_maps_to_unknown(self):
        result = self.synthesize([opinion("Custom", state="ACCUMULATION")])

        self.assertEqual(result.trend, TrendState.UNKNOWN)
        self.assertTrue(any("mapped to UNKNOWN" in item for item in result.warnings))

    def test_state_tie_returns_unknown_and_warning(self):
        result = self.synthesize(
            [opinion("Trend", state="TREND"), opinion("Correction", state="CORRECTION")]
        )

        self.assertEqual(result.trend, TrendState.UNKNOWN)
        self.assertTrue(any("State disagreement" in item for item in result.warnings))

    def test_duplicate_expert_names_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate expert opinion"):
            self.synthesize([opinion("Trend"), opinion("Trend")])

    def test_invalid_input_type_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "ExpertOpinion"):
            self.synthesize([object()])

    def test_non_iterable_input_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "iterable"):
            self.synthesize(None)

    def test_generator_input_is_accepted(self):
        values = (item for item in [opinion("Trend", Direction.BULLISH, "TREND")])

        result = self.synthesize(values)

        self.assertEqual(result.direction, Direction.BULLISH)

    def test_zero_configured_weight_excludes_opinion(self):
        values = [
            opinion("Bull", Direction.BULLISH, "TREND"),
            opinion("Bear", Direction.BEARISH, "REVERSAL"),
        ]

        result = self.synthesize(values, weights={"Bull": 0.0})

        self.assertEqual(result.direction, Direction.BEARISH)
        self.assertEqual(result.trend, TrendState.REVERSAL)

    def test_all_effective_weights_zero_returns_empty_metrics(self):
        values = [opinion("One"), opinion("Two")]

        result = self.synthesize(values, weights={"One": 0.0, "Two": 0.0})

        self.assertEqual(result.direction, Direction.NEUTRAL)
        self.assertEqual(result.strength, 0.0)
        self.assertTrue(any("positive effective weight" in item for item in result.warnings))

    def test_fixed_timestamp_round_trips(self):
        result = self.synthesize([opinion("Trend")])

        restored = MarketState.from_dict(result.to_dict())

        self.assertEqual(restored, result)
        self.assertEqual(restored.timestamp, FIXED_TIME)

    def test_aware_timestamp_is_normalized_to_utc(self):
        supplied = datetime(2026, 7, 13, 14, 0, tzinfo=timezone(timedelta(hours=2)))

        result = self.engine.synthesize([], timestamp=supplied)

        self.assertEqual(result.timestamp, FIXED_TIME)
        self.assertIs(result.timestamp.tzinfo, timezone.utc)

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            self.engine.synthesize([], timestamp=datetime(2026, 7, 13, 12, 0))

    def test_reasons_are_prefixed_and_deduplicated_deterministically(self):
        values = [
            opinion("Trend", reasons=["Structure intact", "Structure intact"]),
            opinion("Flow", reasons=["Inflow elevated"]),
        ]

        result = self.synthesize(values)

        self.assertEqual(
            result.reasons,
            ("Trend: Structure intact", "Flow: Inflow elevated"),
        )

    def test_low_quality_and_insufficient_contributor_warnings(self):
        result = self.synthesize(
            [opinion("Weak", Direction.BULLISH, "TREND", confidence=40, quality=30)]
        )

        self.assertTrue(any("Low aggregate quality" in item for item in result.warnings))
        self.assertTrue(any("Insufficient contributors" in item for item in result.warnings))

    def test_all_output_metrics_are_bounded(self):
        result = self.synthesize(
            [
                opinion("Trend", Direction.BULLISH, "TREND", score=100, confidence=100, quality=100),
                opinion("Flow", Direction.BEARISH, "REVERSAL", score=0, confidence=1, quality=1),
            ]
        )

        for value in (
            result.strength,
            result.continuation_probability,
            result.correction_probability,
            result.reversal_probability,
            result.market_maturity,
            result.decision_stability,
            result.overall_confidence,
        ):
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 100.0)

    def test_identical_input_and_timestamp_are_deterministic(self):
        values = [
            opinion("Trend", Direction.BULLISH, "TREND"),
            opinion("Flow", Direction.NEUTRAL, "CORRECTION"),
        ]

        first = self.synthesize(values)
        second = self.synthesize(values)

        self.assertEqual(first, second)

    def test_incoming_opinions_remain_unchanged(self):
        value = opinion("Trend", Direction.BULLISH, "TREND", reasons=["Stable"])
        before = value.to_dict()

        self.synthesize([value], weights={"Trend": 2.0})

        self.assertEqual(value.to_dict(), before)

    def test_unknown_weight_keys_are_ignored_with_warning(self):
        result = self.synthesize(
            [opinion("Trend", Direction.BULLISH, "TREND")],
            weights={"Missing": 5.0},
        )

        self.assertEqual(result.direction, Direction.BULLISH)
        self.assertTrue(any("unknown expert 'Missing'" in item for item in result.warnings))

    def test_synthesis_safety_warnings_are_retained_when_output_is_capped(self):
        values = [
            opinion("Bull", Direction.BULLISH, "TREND"),
            opinion("Bear", Direction.BEARISH, "REVERSAL"),
        ]
        unknown_weights = {"Missing%02d" % index: 1.0 for index in range(25)}

        result = self.synthesize(values, weights=unknown_weights)

        self.assertEqual(len(result.warnings), self.engine.policy.warning_limit)
        self.assertIn(
            "Material direction conflict: bullish and bearish support are both meaningful.",
            result.warnings,
        )
        self.assertIn(
            "State disagreement: multiple states have meaningful support without a clear winner.",
            result.warnings,
        )

    def test_invalid_weights_are_rejected(self):
        for invalid in (-1.0, float("nan"), float("inf"), True):
            with self.subTest(invalid=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    self.synthesize([opinion("Trend")], weights={"Trend": invalid})

    def test_one_strong_expert_overrides_several_weak_experts(self):
        values = [
            opinion("Strong", Direction.BULLISH, "TREND", confidence=100, quality=100),
            opinion("Weak1", Direction.BEARISH, "REVERSAL", confidence=10, quality=10),
            opinion("Weak2", Direction.BEARISH, "REVERSAL", confidence=10, quality=10),
            opinion("Weak3", Direction.BEARISH, "REVERSAL", confidence=10, quality=10),
        ]

        result = self.synthesize(values)

        self.assertEqual(result.direction, Direction.BULLISH)
        self.assertEqual(result.trend, TrendState.TREND)

    def test_probabilities_are_support_scores_not_required_to_sum_to_100(self):
        values = [
            opinion("Trend", state="TREND"),
            opinion("Range", state="RANGE"),
        ]

        result = self.synthesize(values)
        reported_sum = (
            result.continuation_probability
            + result.correction_probability
            + result.reversal_probability
        )

        self.assertLess(reported_sum, 100.0)

    def test_custom_policy_is_validated_and_applied(self):
        engine = MarketStateEngine(SynthesisPolicy(direction_threshold=0.90))
        values = [
            opinion("Bull", Direction.BULLISH, "TREND", confidence=90, quality=90),
            opinion("Neutral", Direction.NEUTRAL, "TREND", confidence=90, quality=90),
        ]

        result = engine.synthesize(values, timestamp=FIXED_TIME)

        self.assertEqual(result.direction, Direction.NEUTRAL)


if __name__ == "__main__":
    unittest.main()
