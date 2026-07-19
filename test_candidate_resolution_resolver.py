import unittest

from app.intelligence.candidate_resolution.enums import (
    CandidateResolutionType,
)

from app.intelligence.candidate_resolution.resolver import (
    CandidateResolver,
)


class TestCandidateResolver(unittest.TestCase):

    def test_exact_resolution(self):
        result = CandidateResolver().resolve(
            candidate_a_id="cand_001",
            candidate_b_id="cand_002",
            identity_match=True,
            time_window_match=True,
        )

        self.assertEqual(
            result.resolution_type,
            CandidateResolutionType.EXACT_MATCH,
        )

        self.assertEqual(
            result.canonical_candidate_id,
            "cand_001",
        )

    def test_merge_resolution(self):
        result = CandidateResolver().resolve(
            candidate_a_id="cand_002",
            candidate_b_id="cand_003",
            identity_match=True,
            time_window_match=False,
        )

        self.assertEqual(
            result.resolution_type,
            CandidateResolutionType.MERGE_ALLOWED,
        )

        self.assertEqual(
            len(result.merged_candidate_ids),
            2,
        )

    def test_keep_separate(self):
        result = CandidateResolver().resolve(
            candidate_a_id="cand_001",
            candidate_b_id="cand_002",
            identity_match=False,
            time_window_match=False,
        )

        self.assertEqual(
            result.resolution_type,
            CandidateResolutionType.KEEP_SEPARATE,
        )


if __name__ == "__main__":
    unittest.main()
