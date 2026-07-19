import unittest

from app.intelligence.candidate_projection import (
    CandidateProjectionProjector,
    CandidateProjectionStatus,
    CandidateProjectionVersion,
)


class TestCandidateIntelligenceProjection(
    unittest.TestCase
):

    def test_project_creates_projection(self) -> None:
        result = CandidateProjectionProjector().project(
            candidate_id="candidate_001",
            lifecycle_state="ACTIVE",
            resolution_state="RESOLVED",
            completeness_state="COMPLETE",
            evidence_reference_ids=(
                "obs_001",
            ),
            attachment_reference_ids=(
                "attachment_001",
            ),
        )

        self.assertEqual(
            result.candidate_id,
            "candidate_001",
        )

        self.assertEqual(
            result.lifecycle_state,
            "ACTIVE",
        )

        self.assertEqual(
            result.resolution_state,
            "RESOLVED",
        )

        self.assertIs(
            result.status,
            CandidateProjectionStatus.AVAILABLE,
        )

        self.assertIs(
            result.version,
            CandidateProjectionVersion.V1,
        )

    def test_projection_is_read_only(self) -> None:
        result = CandidateProjectionProjector().project(
            candidate_id="candidate_001",
            lifecycle_state="ACTIVE",
            resolution_state="RESOLVED",
            completeness_state="COMPLETE",
            evidence_reference_ids=(
                "obs_001",
            ),
            attachment_reference_ids=(
                "attachment_001",
            ),
        )

        with self.assertRaises(
            Exception
        ):
            result.candidate_id = "changed"


if __name__ == "__main__":
    unittest.main()
