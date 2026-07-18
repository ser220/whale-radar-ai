import unittest

from app.intelligence.candidate_lifecycle.enums import (
    CandidateLifecycleState,
)

from app.intelligence.candidate_lifecycle.policy import (
    CandidateLifecyclePolicy,
)


class TestCandidateLifecyclePolicy(unittest.TestCase):

    def test_allowed_transition(self):
        self.assertTrue(
            CandidateLifecyclePolicy.can_transition(
                CandidateLifecycleState.CREATED,
                CandidateLifecycleState.ACTIVE,
            )
        )

    def test_forbidden_transition(self):
        self.assertFalse(
            CandidateLifecyclePolicy.can_transition(
                CandidateLifecycleState.CREATED,
                CandidateLifecycleState.SUPERSEDED,
            )
        )

    def test_terminal_state_cannot_continue(self):
        self.assertFalse(
            CandidateLifecyclePolicy.can_transition(
                CandidateLifecycleState.EXPIRED,
                CandidateLifecycleState.ACTIVE,
            )
        )

    def test_invalid_transition_raises(self):
        with self.assertRaises(ValueError):
            CandidateLifecyclePolicy.validate_transition(
                CandidateLifecycleState.CREATED,
                CandidateLifecycleState.SUPERSEDED,
            )


if __name__ == "__main__":
    unittest.main()
