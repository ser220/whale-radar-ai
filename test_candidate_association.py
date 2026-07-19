import unittest

from app.intelligence.candidate_association.identity import (
    build_association_identity,
)


class TestCandidateAssociationIdentity(unittest.TestCase):

    def test_same_input_same_identity(self) -> None:
        first = build_association_identity(
            candidate_id="candidate_001",
            situation_event_id="situation_001",
            association_type="PRIMARY",
            reference_version="V1",
        )

        second = build_association_identity(
            candidate_id="candidate_001",
            situation_event_id="situation_001",
            association_type="PRIMARY",
            reference_version="V1",
        )

        self.assertEqual(first, second)

    def test_different_event_changes_identity(self) -> None:
        first = build_association_identity(
            candidate_id="candidate_001",
            situation_event_id="situation_001",
            association_type="PRIMARY",
            reference_version="V1",
        )

        second = build_association_identity(
            candidate_id="candidate_001",
            situation_event_id="situation_002",
            association_type="PRIMARY",
            reference_version="V1",
        )

        self.assertNotEqual(first, second)

    def test_identity_prefix(self) -> None:
        result = build_association_identity(
            candidate_id="candidate_001",
            situation_event_id="situation_001",
            association_type="PRIMARY",
            reference_version="V1",
        )

        self.assertTrue(
            result.startswith("association_")
        )

    def test_required_fields_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_association_identity(
                candidate_id="",
                situation_event_id="situation_001",
                association_type="PRIMARY",
                reference_version="V1",
            )


if __name__ == "__main__":
    unittest.main()
