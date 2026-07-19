import unittest

from app.intelligence.candidate_resolution.enums import (
    CandidateResolutionType,
)

from app.intelligence.candidate_resolution.policy import (
    CandidateResolutionPolicy,
)


class TestCandidateResolutionPolicy(unittest.TestCase):

    def test_exact_match(self):
        result = (
            CandidateResolutionPolicy.resolve_type(
                same_identity=True,
                same_time_window=True,
            )
        )

        self.assertEqual(
            result,
            CandidateResolutionType.EXACT_MATCH,
        )

    def test_merge_allowed(self):
        result = (
            CandidateResolutionPolicy.resolve_type(
                same_identity=True,
                same_time_window=False,
            )
        )

        self.assertEqual(
            result,
            CandidateResolutionType.MERGE_ALLOWED,
        )

    def test_keep_separate(self):
        result = (
            CandidateResolutionPolicy.resolve_type(
                same_identity=False,
                same_time_window=False,
            )
        )

        self.assertEqual(
            result,
            CandidateResolutionType.KEEP_SEPARATE,
        )


if __name__ == "__main__":
    unittest.main()
