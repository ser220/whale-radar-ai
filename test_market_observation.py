import unittest
from datetime import datetime, timezone, timedelta

from app.intelligence.observations import (
    MarketObservation,
    MarketObservationType,
)


def build_observation():
    return MarketObservation(
        source_category="EXCHANGE",
        source="BINANCE",
        symbol="BTCUSDT",
        observation_type=MarketObservationType.PRICE_MOVEMENT,
        severity="MEDIUM",
        value=-2.21,
        reference_value=0.0,
        captured_at=datetime(
            2026,
            7,
            17,
            12,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        ),
    )


class TestMarketObservation(unittest.TestCase):

    def test_immutable_contract(self):
        observation = build_observation()

        with self.assertRaises(Exception):
            observation.value = 10


    def test_timestamp_normalizes_to_utc(self):
        observation = build_observation()

        self.assertEqual(
            observation.captured_at.tzinfo,
            timezone.utc,
        )

        self.assertEqual(
            observation.captured_at.hour,
            10,
        )


    def test_observation_type_validation(self):
        observation = build_observation()

        self.assertEqual(
            observation.observation_type,
            MarketObservationType.PRICE_MOVEMENT,
        )


    def test_serialization_round_trip(self):
        observation = build_observation()

        payload = observation.to_dict()

        restored = MarketObservation.from_dict(
            payload
        )

        self.assertEqual(
            restored,
            observation,
        )


    def test_canonical_json_is_stable(self):
        observation = build_observation()

        first = observation.canonical_json()
        second = observation.canonical_json()

        self.assertEqual(
            first,
            second,
        )


    def test_invalid_numeric_value_rejected(self):
        with self.assertRaises(Exception):
            MarketObservation(
                source_category="EXCHANGE",
                source="BINANCE",
                symbol="BTCUSDT",
                observation_type=MarketObservationType.VOLUME_CHANGE,
                severity="LOW",
                value=float("nan"),
                reference_value=0.0,
                captured_at=datetime.now(timezone.utc),
            )


if __name__ == "__main__":
    unittest.main()
