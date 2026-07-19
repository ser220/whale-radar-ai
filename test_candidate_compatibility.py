import unittest

from app.intelligence.candidate_compatibility import (
    CandidateCompatibilityChecker,
    CandidateCompatibilityStatus,
    CandidateCompatibilityVersion,
)


class TestCandidateCompatibilityChecker(unittest.TestCase):

    def test_check_creates_record(self) -> None:
        result = CandidateCompatibilityChecker().check(
            candidate_reference="candidate:001",
            producer_version="envelope:v1",
            consumer_version="consumer:v1",
        )

        self.assertEqual(
            result.candidate_reference,
            "candidate:001",
        )

        self.assertEqual(
            result.producer_version,
            "envelope:v1",
        )

        self.assertEqual(
            result.consumer_version,
            "consumer:v1",
        )

        self.assertIs(
            result.status,
            CandidateCompatibilityStatus.COMPATIBLE,
        )

        self.assertIs(
            result.compatibility_version,
            CandidateCompatibilityVersion.V1,
        )


    def test_empty_candidate_reference_rejected(
        self,
    ) -> None:

        with self.assertRaises(ValueError):
            CandidateCompatibilityChecker().check(
                candidate_reference="",
                producer_version="envelope:v1",
                consumer_version="consumer:v1",
            )


    def test_record_is_read_only(self) -> None:
        result = CandidateCompatibilityChecker().check(
            candidate_reference="candidate:001",
            producer_version="envelope:v1",
            consumer_version="consumer:v1",
        )

        with self.assertRaises(Exception):
            result.status = (
                CandidateCompatibilityStatus.INCOMPATIBLE
            )


if __name__ == "__main__":
    unittest.main()
