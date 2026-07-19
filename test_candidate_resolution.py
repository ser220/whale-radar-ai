import unittest
from datetime import datetime, timezone

from app.intelligence.candidate_resolution.enums import (
    CandidateResolutionType,
    CandidateResolutionReason,
)

from app.intelligence.candidate_resolution.models import (
    CandidateResolutionRecord,
)


class TestCandidateResolutionRecord(unittest.TestCase):

    def test_exact_fields(self):
        record = CandidateResolutionRecord(
            canonical_candidate_id="cand_001",
            merged_candidate_ids=(
                "cand_001",
                "cand_002",
            ),
            resolution_type=(
                CandidateResolutionType.EXACT_MATCH
            ),
            reason=(
                CandidateResolutionReason.SAME_IDENTITY
            ),
            resolved_at=datetime.now(
                timezone.utc
            ),
        )

        self.assertEqual(
            record.canonical_candidate_id,
            "cand_001",
        )

        self.assertEqual(
            record.resolution_type,
            CandidateResolutionType.EXACT_MATCH,
        )

    def test_immutable_record(self):
        record = CandidateResolutionRecord(
            canonical_candidate_id="cand_001",
            merged_candidate_ids=("cand_002",),
            resolution_type=(
                CandidateResolutionType.MERGE_ALLOWED
            ),
            reason=(
                CandidateResolutionReason.SAME_IDENTITY
            ),
            resolved_at=datetime.now(
                timezone.utc
            ),
        )

        with self.assertRaises(AttributeError):
            record.reason = (
                CandidateResolutionReason.INSUFFICIENT_MATCH
            )

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            CandidateResolutionRecord(
                canonical_candidate_id="cand_001",
                merged_candidate_ids=(),
                resolution_type=(
                    CandidateResolutionType.KEEP_SEPARATE
                ),
                reason=(
                    CandidateResolutionReason.DIFFERENT_SUBJECT
                ),
                resolved_at=datetime.now(),
            )

    def test_reference_list_is_rejected(self):
        with self.assertRaises(TypeError):
            CandidateResolutionRecord(
                canonical_candidate_id="cand_001",
                merged_candidate_ids=[
                    "cand_002"
                ],
                resolution_type=(
                    CandidateResolutionType.MERGE_ALLOWED
                ),
                reason=(
                    CandidateResolutionReason.SAME_IDENTITY
                ),
                resolved_at=datetime.now(
                    timezone.utc
                ),
            )

from app.intelligence.candidate_resolution.identity import (
    build_resolution_identity,
)


class TestCandidateResolutionIdentity(unittest.TestCase):

    def test_same_input_same_identity(self):
        first = build_resolution_identity(
            asset="BTC",
            category="volatility",
            subject="expansion",
            time_window="1h",
        )

        second = build_resolution_identity(
            asset="btc",
            category="VOLATILITY",
            subject="expansion",
            time_window="1h",
        )

        self.assertEqual(
            first,
            second,
        )

    def test_different_subject_changes_identity(self):
        first = build_resolution_identity(
            asset="BTC",
            category="volatility",
            subject="expansion",
            time_window="1h",
        )

        second = build_resolution_identity(
            asset="BTC",
            category="volatility",
            subject="contraction",
            time_window="1h",
        )

        self.assertNotEqual(
            first,
            second,
        )

    def test_prefix(self):
        identity = build_resolution_identity(
            asset="ETH",
            category="trend",
            subject="break",
            time_window="4h",
        )

        self.assertTrue(
            identity.startswith(
                "resolution_"
            )
        )

if __name__ == "__main__":
    unittest.main()
