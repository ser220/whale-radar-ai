import unittest

from app.intelligence.candidate_lifecycle.enums import (
    CandidateLifecycleState,
)

from app.intelligence.candidate_lifecycle.manager import (
    CandidateLifecycleManager,
)


class TestCandidateLifecycleManager(unittest.TestCase):

    def test_create_record(self):
        manager = CandidateLifecycleManager()

        record = manager.create(
            "cand_001"
        )

        self.assertEqual(
            record.state,
            CandidateLifecycleState.CREATED,
        )

    def test_valid_transition(self):
        manager = CandidateLifecycleManager()

        record = manager.create(
            "cand_001"
        )

        updated = manager.transition(
            record,
            CandidateLifecycleState.ACTIVE,
            reason="activated",
        )

        self.assertEqual(
            updated.state,
            CandidateLifecycleState.ACTIVE,
        )

        self.assertEqual(
            updated.previous_state,
            CandidateLifecycleState.CREATED,
        )

    def test_invalid_transition_rejected(self):
        manager = CandidateLifecycleManager()

        record = manager.create(
            "cand_001"
        )

        with self.assertRaises(ValueError):
            manager.transition(
                record,
                CandidateLifecycleState.SUPERSEDED,
            )


if __name__ == "__main__":
    unittest.main()
