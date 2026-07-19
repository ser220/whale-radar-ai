import unittest
from datetime import datetime, timezone

from app.intelligence.candidate_association import (
    AssociationReferenceVersion,
    CandidateAssociationBuilder,
    CandidateAssociationType,
)


class TestCandidateAssociationBuilder(unittest.TestCase):

    def test_build_creates_association(self) -> None:
        now = datetime.now(timezone.utc)

        builder = CandidateAssociationBuilder()

        result = builder.build(
            candidate_id="candidate_001",
            situation_event_id="situation_001",
            association_type=CandidateAssociationType.PRIMARY,
            created_at=now,
        )

        self.assertEqual(
            result.candidate_id,
            "candidate_001",
        )

        self.assertEqual(
            result.situation_event_id,
            "situation_001",
        )

        self.assertIs(
            result.association_type,
            CandidateAssociationType.PRIMARY,
        )

        self.assertIs(
            result.reference_version,
            AssociationReferenceVersion.V1,
        )

        self.assertEqual(
            result.created_at,
            now,
        )

    def test_default_version_is_v1(self) -> None:
        builder = CandidateAssociationBuilder()

        result = builder.build(
            candidate_id="candidate_001",
            situation_event_id="situation_001",
            association_type=CandidateAssociationType.CONTEXT,
        )

        self.assertIs(
            result.reference_version,
            AssociationReferenceVersion.V1,
        )

    def test_invalid_association_type_rejected(self) -> None:
        builder = CandidateAssociationBuilder()

        with self.assertRaises(TypeError):
            builder.build(
                candidate_id="candidate_001",
                situation_event_id="situation_001",
                association_type="PRIMARY",
            )


if __name__ == "__main__":
    unittest.main()
