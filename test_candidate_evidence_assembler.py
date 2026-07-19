import unittest
from datetime import datetime, timezone

from app.intelligence.candidate_evidence import (
    CandidateEvidenceAssembler,
    EvidenceAssemblyVersion,
    EvidenceReference,
    EvidenceReferenceType,
)


class TestCandidateEvidenceAssembler(unittest.TestCase):

    def test_assemble_creates_record(self) -> None:
        now = datetime.now(timezone.utc)

        reference = EvidenceReference(
            reference_id="obs_001",
            reference_type=EvidenceReferenceType.OBSERVATION,
        )

        assembler = CandidateEvidenceAssembler()

        result = assembler.assemble(
            candidate_id="candidate_001",
            evidence_references=(reference,),
            assembled_at=now,
        )

        self.assertEqual(
            result.candidate_id,
            "candidate_001",
        )

        self.assertEqual(
            result.evidence_references,
            (reference,),
        )

        self.assertIs(
            result.assembly_version,
            EvidenceAssemblyVersion.V1,
        )

        self.assertEqual(
            result.assembled_at,
            now,
        )

    def test_default_time_is_created(self) -> None:
        reference = EvidenceReference(
            reference_id="provider_001",
            reference_type=EvidenceReferenceType.PROVIDER,
        )

        result = CandidateEvidenceAssembler().assemble(
            candidate_id="candidate_001",
            evidence_references=(reference,),
        )

        self.assertEqual(
            result.assembled_at.tzinfo,
            timezone.utc,
        )

    def test_empty_references_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CandidateEvidenceAssembler().assemble(
                candidate_id="candidate_001",
                evidence_references=(),
            )


if __name__ == "__main__":
    unittest.main()
