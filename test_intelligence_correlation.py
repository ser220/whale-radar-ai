import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

from app.intelligence.contracts import Direction, ExpertOpinion
from app.intelligence.correlation import EventCorrelation
from app.intelligence.fast import FastEventType, FastObservation


WINDOW_START = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 7, 14, 12, 5, tzinfo=timezone.utc)
CREATED_AT = datetime(2026, 7, 14, 12, 6, tzinfo=timezone.utc)


def correlation(**overrides):
    values = {
        "correlation_id": "corr-btc-001",
        "created_at": CREATED_AT,
        "asset": "BTC",
        "time_window": (WINDOW_START, WINDOW_END),
        "related_fast_events": ("fast-btc-001",),
        "related_observations": ("trend-btc-4h-001",),
        "related_experts": ("legacy_intelligence", "trend_expert"),
        "correlation_score": 88,
        "independence_score": 45,
        "metadata": {
            "shared_event_references": ["market-event-btc-001"],
            "basis": {"same_asset": True, "compatible_timestamps": True},
        },
    }
    values.update(overrides)
    return EventCorrelation(**values)


class EventCorrelationTests(unittest.TestCase):
    def test_valid_correlation(self):
        result = correlation(asset=" btc ")

        self.assertEqual(result.asset, "BTC")
        self.assertEqual(result.correlation_score, 88.0)
        self.assertEqual(result.independence_score, 45.0)
        self.assertIs(result.created_at.tzinfo, timezone.utc)

    def test_multiple_experts_preserve_explicit_order(self):
        result = correlation(
            related_experts=["legacy_intelligence", "trend_expert", "funding_expert"]
        )

        self.assertEqual(
            result.related_experts,
            ("legacy_intelligence", "trend_expert", "funding_expert"),
        )

    def test_fast_and_deep_relationship_uses_stable_references(self):
        fast = FastObservation(
            event_id="fast-btc-001",
            asset="BTC",
            timestamp=WINDOW_START,
            source="normalized-market-events",
            event_type=FastEventType.STRUCTURE_BREAK,
            strength=80,
            quality=90,
            description="A structure break was observed.",
        )
        expert = ExpertOpinion(
            expert_name="trend_expert",
            direction=Direction.BULLISH,
            state="TREND",
            score=80,
            confidence=85,
            quality=90,
            timestamp=WINDOW_END,
        )

        result = correlation(
            asset=fast.asset,
            time_window=(fast.timestamp, expert.timestamp),
            related_fast_events=(fast.event_id,),
            related_experts=(expert.expert_name,),
        )

        self.assertEqual(result.related_fast_events, ("fast-btc-001",))
        self.assertEqual(result.related_experts, ("trend_expert",))
        self.assertEqual(result.time_window, (WINDOW_START, WINDOW_END))

    def test_collections_and_metadata_are_immutable(self):
        fast_events = ["fast-btc-001"]
        metadata = {
            "shared_event_references": ["market-event-btc-001"],
            "basis": {"same_asset": True},
        }
        result = correlation(related_fast_events=fast_events, metadata=metadata)
        fast_events.append("late-event")
        metadata["shared_event_references"].append("late-reference")
        metadata["basis"]["same_asset"] = False

        with self.assertRaises(FrozenInstanceError):
            result.asset = "ETH"
        with self.assertRaises(TypeError):
            result.metadata["new"] = "value"
        with self.assertRaises(TypeError):
            result.metadata["basis"]["same_asset"] = False

        self.assertEqual(result.related_fast_events, ("fast-btc-001",))
        self.assertEqual(
            result.metadata["shared_event_references"],
            ("market-event-btc-001",),
        )
        self.assertTrue(result.metadata["basis"]["same_asset"])

    def test_duplicate_references_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicates"):
            correlation(related_experts=("trend_expert", "trend_expert"))

    def test_invalid_scores_are_rejected(self):
        invalid_values = (-0.01, 100.01, float("nan"), float("inf"), True)
        for value in invalid_values:
            with self.subTest(field="correlation_score", value=value):
                with self.assertRaises((TypeError, ValueError)):
                    correlation(correlation_score=value)
            with self.subTest(field="independence_score", value=value):
                with self.assertRaises((TypeError, ValueError)):
                    correlation(independence_score=value)

    def test_score_boundaries_are_valid(self):
        result = correlation(correlation_score=0, independence_score=100)

        self.assertEqual(result.correlation_score, 0.0)
        self.assertEqual(result.independence_score, 100.0)

    def test_invalid_timestamps_are_rejected(self):
        naive = datetime(2026, 7, 14, 12, 0)
        with self.assertRaisesRegex(ValueError, "created_at.*timezone-aware"):
            correlation(created_at=naive)
        with self.assertRaisesRegex(ValueError, "time_window start.*timezone-aware"):
            correlation(time_window=(naive, WINDOW_END))
        with self.assertRaisesRegex(ValueError, "start must not be after end"):
            correlation(time_window=(WINDOW_END, WINDOW_START))

    def test_aware_timestamps_are_normalized_to_utc(self):
        offset = timezone(timedelta(hours=2))
        result = correlation(
            created_at=datetime(2026, 7, 14, 14, 6, tzinfo=offset),
            time_window=(
                datetime(2026, 7, 14, 14, 0, tzinfo=offset),
                datetime(2026, 7, 14, 14, 5, tzinfo=offset),
            ),
        )

        self.assertEqual(result.created_at, CREATED_AT)
        self.assertEqual(result.time_window, (WINDOW_START, WINDOW_END))
        self.assertIs(result.time_window[0].tzinfo, timezone.utc)

    def test_asset_and_correlation_id_are_required(self):
        with self.assertRaisesRegex(ValueError, "asset"):
            correlation(asset=" ")
        with self.assertRaisesRegex(ValueError, "correlation_id"):
            correlation(correlation_id="")

    def test_serialization_round_trip(self):
        result = correlation()

        payload = result.to_dict()
        restored = EventCorrelation.from_dict(payload)

        self.assertEqual(payload["created_at"], CREATED_AT.isoformat())
        self.assertEqual(payload["time_window"]["start"], WINDOW_START.isoformat())
        self.assertEqual(payload["related_experts"], ["legacy_intelligence", "trend_expert"])
        self.assertEqual(restored, result)

    def test_from_dict_accepts_zulu_timestamps(self):
        payload = correlation().to_dict()
        payload["created_at"] = "2026-07-14T12:06:00Z"
        payload["time_window"] = {
            "start": "2026-07-14T12:00:00Z",
            "end": "2026-07-14T12:05:00Z",
        }

        restored = EventCorrelation.from_dict(payload)

        self.assertEqual(restored.created_at, CREATED_AT)
        self.assertEqual(restored.time_window, (WINDOW_START, WINDOW_END))


if __name__ == "__main__":
    unittest.main()
