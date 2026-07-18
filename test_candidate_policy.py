import unittest

from app.intelligence.candidates.policy import (
    CandidateIdentityPolicy,
)


class TestCandidateIdentityPolicy(unittest.TestCase):

    def test_default_policy(self):
        policy = CandidateIdentityPolicy()

        self.assertEqual(
            policy.version,
            "v1",
        )

    def test_supported_policy(self):
        policy = CandidateIdentityPolicy()

        policy.validate()

    def test_unknown_policy_rejected(self):
        policy = CandidateIdentityPolicy(
            version="v99"
        )

        with self.assertRaises(ValueError):
            policy.validate()


if __name__ == "__main__":
    unittest.main()
