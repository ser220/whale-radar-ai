import unittest

from app.intelligence.candidate_decision_input import (
    CandidateDecisionInputProjector,
    CandidateDecisionInputStatus,
    CandidateDecisionInputVersion,
)


class TestCandidateDecisionInputProjector(unittest.TestCase):

    def test_project_creates_projection(self) -> None:
        result = CandidateDecisionInputProjector().project(
            candidate_reference="candidate:001",
            intelligence_reference=(
                "envelope:candidate:001:v1"
            ),
        )

        self.assertEqual(
            result.candidate_reference,
            "candidate:001",
        )

        self.assertEqual(
            result.intelligence_reference,
            "envelope:candidate:001:v1",
        )

        self.assertIs(
            result.status,
            CandidateDecisionInputStatus.AVAILABLE,
        )

        self.assertIs(
            result.version,
            CandidateDecisionInputVersion.V1,
        )


    def test_empty_intelligence_reference_rejected(
        self,
    ) -> None:

        with self.assertRaises(ValueError):
            CandidateDecisionInputProjector().project(
                candidate_reference="candidate:001",
                intelligence_reference="",
            )


    def test_projection_is_read_only(self) -> None:
        result = CandidateDecisionInputProjector().project(
            candidate_reference="candidate:001",
            intelligence_reference=(
                "envelope:candidate:001:v1"
            ),
        )

        with self.assertRaises(Exception):
            result.status = (
                CandidateDecisionInputStatus.UNAVAILABLE
            )


if __name__ == "__main__":
    unittest.main()
