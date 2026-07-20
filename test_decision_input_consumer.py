import unittest

from app.intelligence.decision_input_consumer import (
    DecisionInputConsumer,
    DecisionInputConsumerStatus,
    DecisionInputConsumerVersion,
)


class TestDecisionInputConsumer(unittest.TestCase):

    def test_consume_creates_record(self):

        result = DecisionInputConsumer().consume(
            input_reference="decision-input:candidate:001:v1",
        )

        self.assertEqual(
            result.input_reference,
            "decision-input:candidate:001:v1",
        )

        self.assertIs(
            result.status,
            DecisionInputConsumerStatus.AVAILABLE,
        )

        self.assertIs(
            result.version,
            DecisionInputConsumerVersion.V1,
        )


    def test_empty_reference_rejected(self):

        with self.assertRaises(ValueError):
            DecisionInputConsumer().consume(
                input_reference="",
            )


    def test_record_is_read_only(self):

        result = DecisionInputConsumer().consume(
            input_reference="decision-input:candidate:001:v1",
        )

        with self.assertRaises(Exception):
            result.status = (
                DecisionInputConsumerStatus.UNAVAILABLE
            )


if __name__ == "__main__":
    unittest.main()
