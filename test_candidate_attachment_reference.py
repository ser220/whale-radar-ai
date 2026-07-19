import unittest
from datetime import datetime, timezone

from app.intelligence.candidate_attachment import (
    CandidateAttachmentReferenceBuilder,
    CandidateAttachmentType,
    CandidateAttachmentReferenceVersion,
)


class TestCandidateAttachmentReferenceBuilder(unittest.TestCase):

    def test_build_creates_reference(self) -> None:
        created_at = datetime.now(timezone.utc)

        result = CandidateAttachmentReferenceBuilder().build(
            candidate_id="candidate_001",
            attachment_id="reality_gap_attachment_001",
            attachment_type=(
                CandidateAttachmentType.REALITY_GAP_ANALYSIS
            ),
            created_at=created_at,
        )

        self.assertEqual(
            result.candidate_id,
            "candidate_001",
        )

        self.assertEqual(
            result.attachment_id,
            "reality_gap_attachment_001",
        )

        self.assertIs(
            result.attachment_type,
            CandidateAttachmentType.REALITY_GAP_ANALYSIS,
        )

        self.assertIs(
            result.reference_version,
            CandidateAttachmentReferenceVersion.V1,
        )

        self.assertEqual(
            result.created_at,
            created_at,
        )

    def test_default_time_is_created(self) -> None:
        result = CandidateAttachmentReferenceBuilder().build(
            candidate_id="candidate_001",
            attachment_id="attachment_001",
            attachment_type=(
                CandidateAttachmentType.REALITY_GAP_ANALYSIS
            ),
        )

        self.assertEqual(
            result.created_at.tzinfo,
            timezone.utc,
        )

    def test_empty_attachment_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CandidateAttachmentReferenceBuilder().build(
                candidate_id="candidate_001",
                attachment_id="",
                attachment_type=(
                    CandidateAttachmentType.REALITY_GAP_ANALYSIS
                ),
            )


if __name__ == "__main__":
    unittest.main()
