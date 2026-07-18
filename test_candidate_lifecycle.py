import unittest
from datetime import datetime, timezone

from app.intelligence.candidate_lifecycle.enums import (
    CandidateLifecycleState,
)

from app.intelligence.candidate_lifecycle.models import (
    CandidateLifecycleRecord,
)


class TestCandidateLifecycleRecord(unittest.TestCase):

    def test_exact_fields(self):
        record = CandidateLifecycleRecord(
            candidate_id="cand_test_001",
            state=CandidateLifecycleState.CREATED,
            changed_at=datetime.now(timezone.utc),
        )

        self.assertEqual(
            record.candidate_id,
            "cand_test_001",
        )

        self.assertEqual(
            record.state,
            CandidateLifecycleState.CREATED,
        )

    def test_immutable_contract(self):
        record = CandidateLifecycleRecord(
            candidate_id="cand_test_001",
            state=CandidateLifecycleState.CREATED,
            changed_at=datetime.now(timezone.utc),
        )

        with self.assertRaises(AttributeError):
            record.state = CandidateLifecycleState.ACTIVE

    def test_timestamp_is_utc(self):
        dt = datetime(
            2026,
            7,
            18,
            12,
            0,
            tzinfo=timezone.utc,
        )

        record = CandidateLifecycleRecord(
            candidate_id="cand_test_001",
            state=CandidateLifecycleState.ACTIVE,
            changed_at=dt,
        )

        self.assertEqual(
            record.changed_at.tzinfo,
            timezone.utc,
        )

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            CandidateLifecycleRecord(
                candidate_id="cand_test_001",
                state=CandidateLifecycleState.CREATED,
                changed_at=datetime.now(),
            )

    def test_candidate_id_required(self):
        with self.assertRaises(ValueError):
            CandidateLifecycleRecord(
                candidate_id="",
                state=CandidateLifecycleState.CREATED,
                changed_at=datetime.now(timezone.utc),
            )


if __name__ == "__main__":
    unittest.main()
