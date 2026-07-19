import unittest
from datetime import datetime, timezone

from app.intelligence.candidate_evidence import (
    CandidateEvidenceAssembly,
    EvidenceAssemblyVersion,
    EvidenceReference,
    EvidenceReferenceType,
)


class TestCandidateEvidenceAssembly(unittest.TestCase):

    def test_immutable_record(self) -> None:
        reference = EvidenceReference(
            reference_id="obs_001",
            reference_type=EvidenceReferenceType.OBSERVATION,
        )

        record = CandidateEvidenceAssembly(
            candidate_id="candidate_001",
            evidence_references=(reference,),
            assembly_version=EvidenceAssemblyVersion.V1,
            assembled_at=datetime.now(timezone.utc),
        )

        with self.assertRaises(
            AttributeError
        ):
            record.candidate_id = "changed"

    def test_naive_timestamp_rejected(self) -> None:
        reference = EvidenceReference(
            reference_id="obs_001",
            reference_type=EvidenceReferenceType.OBSERVATION,
        )

        with self.assertRaises(ValueError):
            CandidateEvidenceAssembly(
                candidate_id="candidate_001",
                evidence_references=(reference,),
                assembly_version=EvidenceAssemblyVersion.V1,
                assembled_at=datetime.now(),
            )

    def test_duplicate_references_rejected(self) -> None:
        reference = EvidenceReference(
            reference_id="obs_001",
            reference_type=EvidenceReferenceType.OBSERVATION,
        )

        with self.assertRaises(ValueError):
            CandidateEvidenceAssembly(
                candidate_id="candidate_001",
                evidence_references=(
                    reference,
                    reference,
                ),
                assembly_version=EvidenceAssemblyVersion.V1,
                assembled_at=datetime.now(timezone.utc),
            )


if __name__ == "__main__":
    unittest.main()
