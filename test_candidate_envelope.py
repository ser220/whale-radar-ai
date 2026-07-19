import unittest

from app.intelligence.candidate_envelope import (
    CandidateEnvelopeBuilder,
    CandidateEnvelopeStatus,
    CandidateEnvelopeVersion,
)


class TestCandidateEnvelopeBuilder(unittest.TestCase):

    def test_build_creates_envelope(self) -> None:
        result = CandidateEnvelopeBuilder().build(
            envelope_id="env_001",
            candidate_id="candidate_001",
            projection_reference=(
                "projection:candidate_001:v1"
            ),
        )

        self.assertEqual(
            result.envelope_id,
            "env_001",
        )

        self.assertEqual(
            result.candidate_id,
            "candidate_001",
        )

        self.assertEqual(
            result.projection_reference,
            "projection:candidate_001:v1",
        )

        self.assertIs(
            result.status,
            CandidateEnvelopeStatus.AVAILABLE,
        )

        self.assertIs(
            result.version,
            CandidateEnvelopeVersion.V1,
        )


    def test_empty_projection_reference_rejected(
        self,
    ) -> None:

        with self.assertRaises(ValueError):
            CandidateEnvelopeBuilder().build(
                envelope_id="env_001",
                candidate_id="candidate_001",
                projection_reference="",
            )


    def test_envelope_is_read_only(self) -> None:
        result = CandidateEnvelopeBuilder().build(
            envelope_id="env_001",
            candidate_id="candidate_001",
            projection_reference=(
                "projection:candidate_001:v1"
            ),
        )

        with self.assertRaises(Exception):
            result.candidate_id = "changed"


if __name__ == "__main__":
    unittest.main()
