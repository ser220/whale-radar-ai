import unittest
from datetime import datetime, timezone

from app.intelligence.candidates import (
    CandidateBuilder,
    CandidateCategory,
    CandidateStatus,
)


class TestCandidateBuilder(unittest.TestCase):

    def test_build_creates_candidate(self):
        builder = CandidateBuilder()

        candidate = builder.build(
            category=CandidateCategory.MARKET,
            subject="BTCUSDT",
            hypothesis_reference="event-001",
            description="Liquidity transition candidate",
            created_at=datetime(
                2026,
                1,
                1,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        )

        self.assertEqual(
            candidate.status,
            CandidateStatus.CREATED,
        )

        self.assertEqual(
            candidate.candidate_version,
            1,
        )

        self.assertTrue(
            candidate.candidate_id.startswith(
                "candidate-"
            )
        )

    def test_same_input_same_candidate_id(self):
        builder = CandidateBuilder()

        first = builder.build(
            category=CandidateCategory.MARKET,
            subject="BTCUSDT",
            hypothesis_reference="event-001",
            description="Test",
            created_at=datetime(
                2026,
                1,
                1,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        )

        second = builder.build(
            category=CandidateCategory.MARKET,
            subject="BTCUSDT",
            hypothesis_reference="event-001",
            description="Different text",
            created_at=datetime(
                2026,
                1,
                1,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        )

        self.assertEqual(
            first.candidate_id,
            second.candidate_id,
        )

    def test_policy_versions_are_preserved(self):
        builder = CandidateBuilder(
            identity_policy_version="v1",
            candidate_policy_version="v1",
        )

        candidate = builder.build(
            category=CandidateCategory.STRUCTURE,
            subject="ETHUSDT",
            hypothesis_reference="event-002",
            description="Structure candidate",
            created_at=datetime(
                2026,
                1,
                1,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        )

        self.assertEqual(
            candidate.candidate_identity_policy_version,
            "v1",
        )

        self.assertEqual(
            candidate.candidate_policy_version,
            "v1",
        )


if __name__ == "__main__":
    unittest.main()
