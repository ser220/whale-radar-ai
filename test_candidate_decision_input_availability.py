import unittest

from app.intelligence.candidate_decision_availability import (
    CandidateDecisionInputAvailabilityChecker,
    CandidateDecisionInputAvailabilityStatus,
    CandidateDecisionInputAvailabilityVersion,
)


class TestCandidateDecisionInputAvailabilityChecker(unittest.TestCase):

    def test_check_creates_record(self):

        result = CandidateDecisionInputAvailabilityChecker().check(
            input_reference="decision-input:candidate:001:v1",
        )

        self.assertEqual(
            result.input_reference,
            "decision-input:candidate:001:v1",
        )

        self.assertIs(
            result.status,
            CandidateDecisionInputAvailabilityStatus.AVAILABLE,
        )

        self.assertIs(
            result.version,
            CandidateDecisionInputAvailabilityVersion.V1,
        )


    def test_empty_reference_rejected(self):

        with self.assertRaises(ValueError):
            CandidateDecisionInputAvailabilityChecker().check(
                input_reference="",
            )


    def test_record_is_read_only(self):

        result = CandidateDecisionInputAvailabilityChecker().check(
            input_reference="decision-input:candidate:001:v1",
        )

        with self.assertRaises(Exception):
            result.status = (
                CandidateDecisionInputAvailabilityStatus.UNAVAILABLE
            )


if __name__ == "__main__":
    unittest.main()
