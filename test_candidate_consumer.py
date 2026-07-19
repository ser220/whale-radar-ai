import unittest

from app.intelligence.candidate_consumer import (
    CandidateIntelligenceConsumer,
    CandidateConsumerStatus,
    CandidateConsumerVersion,
)


class TestCandidateIntelligenceConsumer(unittest.TestCase):

    def test_consume_creates_contract(self) -> None:
        result = CandidateIntelligenceConsumer().consume(
            consumer_id="consumer_001",
            envelope_reference=(
                "envelope:candidate_001:v1"
            ),
        )

        self.assertEqual(
            result.consumer_id,
            "consumer_001",
        )

        self.assertEqual(
            result.envelope_reference,
            "envelope:candidate_001:v1",
        )

        self.assertIs(
            result.status,
            CandidateConsumerStatus.AVAILABLE,
        )

        self.assertIs(
            result.version,
            CandidateConsumerVersion.V1,
        )


    def test_empty_envelope_reference_rejected(
        self,
    ) -> None:

        with self.assertRaises(ValueError):
            CandidateIntelligenceConsumer().consume(
                consumer_id="consumer_001",
                envelope_reference="",
            )


    def test_contract_is_read_only(self) -> None:
        result = CandidateIntelligenceConsumer().consume(
            consumer_id="consumer_001",
            envelope_reference=(
                "envelope:candidate_001:v1"
            ),
        )

        with self.assertRaises(Exception):
            result.consumer_id = "changed"


if __name__ == "__main__":
    unittest.main()
