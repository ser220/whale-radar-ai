import unittest

from app.intelligence.candidates.identity import (
    build_candidate_id,
)


class TestCandidateIdentity(unittest.TestCase):

    def test_same_input_same_id(self):
        first = build_candidate_id(
            subject="BTCUSDT",
            category="MARKET",
            hypothesis_reference="event-1",
            identity_policy_version="v1",
        )

        second = build_candidate_id(
            subject="BTCUSDT",
            category="MARKET",
            hypothesis_reference="event-1",
            identity_policy_version="v1",
        )

        self.assertEqual(first, second)

    def test_different_subject_changes_id(self):
        first = build_candidate_id(
            subject="BTCUSDT",
            category="MARKET",
            hypothesis_reference="event-1",
            identity_policy_version="v1",
        )

        second = build_candidate_id(
            subject="ETHUSDT",
            category="MARKET",
            hypothesis_reference="event-1",
            identity_policy_version="v1",
        )

        self.assertNotEqual(first, second)

    def test_prefix(self):
        candidate_id = build_candidate_id(
            subject="BTCUSDT",
            category="MARKET",
            hypothesis_reference="event-1",
            identity_policy_version="v1",
        )

        self.assertTrue(
            candidate_id.startswith("candidate-")
        )


if __name__ == "__main__":
    unittest.main()
