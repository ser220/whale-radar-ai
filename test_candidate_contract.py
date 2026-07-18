import unittest
from datetime import datetime, timezone

from app.intelligence.candidates.enums import (
    CandidateCategory,
    CandidateStatus,
)
from app.intelligence.candidates.models import CandidateHypothesis


def build_candidate():
    return CandidateHypothesis(
        candidate_id="cand-001",
        candidate_version=1,
        candidate_identity_policy_version="v1",
        candidate_policy_version="v1",
        category=CandidateCategory.MARKET,
        subject="BTCUSDT",
        hypothesis_reference="market.event.001",
        description="Liquidity transition candidate",
        status=CandidateStatus.CREATED,
        supporting_evidence_refs=["obs-1"],
        contradicting_evidence_refs=["obs-2"],
        limitation_references=["limit-1"],
        created_at=datetime(
            2026,
            1,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
        metadata={
            "source": "test",
        },
    )


class TestCandidateHypothesis(unittest.TestCase):

    def test_exact_fields(self):
        self.assertEqual(
            set(CandidateHypothesis.__dataclass_fields__.keys()),
            {
                "candidate_id",
                "candidate_version",
                "candidate_identity_policy_version",
                "candidate_policy_version",
                "category",
                "subject",
                "hypothesis_reference",
                "description",
                "status",
                "supporting_evidence_refs",
                "contradicting_evidence_refs",
                "limitation_references",
                "created_at",
                "metadata",
            },
        )

    def test_immutable_contract(self):
        candidate = build_candidate()

        with self.assertRaises(Exception):
            candidate.subject = "ETHUSDT"

    def test_timestamp_normalizes_to_utc(self):
        candidate = build_candidate()

        self.assertEqual(
            candidate.created_at.tzinfo,
            timezone.utc,
        )

    def test_reference_lists_are_immutable(self):
        candidate = build_candidate()

        self.assertIsInstance(
            candidate.supporting_evidence_refs,
            tuple,
        )

    def test_metadata_is_frozen(self):
        candidate = build_candidate()

        with self.assertRaises(TypeError):
            candidate.metadata["x"] = "y"

    def test_serialization(self):
        candidate = build_candidate()

        payload = candidate.to_dict()

        self.assertEqual(
            payload["candidate_id"],
            "cand-001",
        )

        self.assertEqual(
            payload["status"],
            "CREATED",
        )


if __name__ == "__main__":
    unittest.main()
