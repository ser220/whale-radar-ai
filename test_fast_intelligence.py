import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

from app.intelligence.fast import FastEventType, FastObservation


UTC_TIME = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


def observation(**overrides):
    values = {
        "event_id": "btc-breakout-001",
        "asset": "BTC",
        "timestamp": UTC_TIME,
        "source": "normalized-market-events",
        "event_type": FastEventType.BREAKOUT,
        "strength": 82,
        "quality": 91,
        "description": "Price moved above the observed range boundary.",
        "metadata": {
            "timeframe": "5m",
            "references": ["event-001", "event-002"],
            "context": {"complete": False},
        },
    }
    values.update(overrides)
    return FastObservation(**values)


class FastObservationTests(unittest.TestCase):
    def test_valid_observation(self):
        result = observation(asset=" btc ", event_type="BREAKOUT")

        self.assertEqual(result.asset, "BTC")
        self.assertEqual(result.event_type, FastEventType.BREAKOUT)
        self.assertEqual(result.strength, 82.0)
        self.assertEqual(result.quality, 91.0)
        self.assertIs(result.timestamp.tzinfo, timezone.utc)

    def test_invalid_asset_is_rejected(self):
        for value in ("", "   ", None):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    observation(asset=value)

    def test_source_and_event_id_are_required(self):
        with self.assertRaisesRegex(ValueError, "source"):
            observation(source=" ")
        with self.assertRaisesRegex(ValueError, "event_id"):
            observation(event_id="")

    def test_naive_and_invalid_timestamps_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            observation(timestamp=datetime(2026, 7, 14, 12, 0))
        with self.assertRaisesRegex(TypeError, "datetime"):
            observation(timestamp="2026-07-14T12:00:00+00:00")

    def test_aware_timestamp_is_normalized_to_utc(self):
        local_time = datetime(
            2026,
            7,
            14,
            14,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        )

        result = observation(timestamp=local_time)

        self.assertEqual(result.timestamp, UTC_TIME)
        self.assertIs(result.timestamp.tzinfo, timezone.utc)

    def test_strength_accepts_boundaries_and_rejects_invalid_values(self):
        self.assertEqual(observation(strength=0).strength, 0.0)
        self.assertEqual(observation(strength=100).strength, 100.0)

        for value in (-0.01, 100.01, float("nan"), float("inf"), True):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    observation(strength=value)

    def test_quality_accepts_boundaries_and_rejects_invalid_values(self):
        self.assertEqual(observation(quality=0).quality, 0.0)
        self.assertEqual(observation(quality=100).quality, 100.0)

        for value in (-1, 101, float("nan"), float("inf"), False):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    observation(quality=value)

    def test_model_and_metadata_are_immutable(self):
        metadata = {
            "references": ["event-001"],
            "context": {"complete": False},
        }
        result = observation(metadata=metadata)
        metadata["references"].append("late-mutation")
        metadata["context"]["complete"] = True

        with self.assertRaises(FrozenInstanceError):
            result.strength = 1
        with self.assertRaises(TypeError):
            result.metadata["new"] = "value"
        with self.assertRaises(TypeError):
            result.metadata["context"]["complete"] = True

        self.assertEqual(result.metadata["references"], ("event-001",))
        self.assertFalse(result.metadata["context"]["complete"])

    def test_serialization_round_trip_preserves_enum_timestamp_and_metadata(self):
        result = observation()

        payload = result.to_dict()
        restored = FastObservation.from_dict(payload)

        self.assertEqual(payload["event_type"], "BREAKOUT")
        self.assertEqual(payload["timestamp"], UTC_TIME.isoformat())
        self.assertEqual(payload["metadata"]["references"], ["event-001", "event-002"])
        self.assertEqual(restored, result)
        self.assertIs(restored.timestamp.tzinfo, timezone.utc)

    def test_from_dict_accepts_zulu_timestamp(self):
        payload = observation().to_dict()
        payload["timestamp"] = "2026-07-14T12:00:00Z"

        restored = FastObservation.from_dict(payload)

        self.assertEqual(restored.timestamp, UTC_TIME)

    def test_all_initial_event_types_are_public(self):
        self.assertEqual(
            [item.value for item in FastEventType],
            [
                "BREAKOUT",
                "STRUCTURE_BREAK",
                "VOLUME_EXPANSION",
                "LIQUIDITY_EVENT",
                "MOMENTUM_SHIFT",
            ],
        )

    def test_unknown_event_type_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "event_type"):
            observation(event_type="BUY_SIGNAL")


if __name__ == "__main__":
    unittest.main()
