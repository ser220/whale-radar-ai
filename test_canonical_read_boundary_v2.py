"""Focused tests for the lossless canonical attachment read boundary v2."""

from dataclasses import FrozenInstanceError, fields
import json
import unittest

from app.intelligence.attachments import (
    ArtifactReferenceValidationError,
    AttachmentAvailabilityStatus,
    AttachmentReadV2ValidationError,
    RealityGapArtifactReference,
    RealityGapArtifactType,
    RealityGapAttachmentReadReferenceV2,
)


CLASSIFICATION_DIGEST = "sha256:" + ("a" * 64)
METRIC_SET_DIGEST = "sha256:" + ("b" * 64)


def artifact(**overrides):
    values = {
        "artifact_type": RealityGapArtifactType.ANALYSIS,
        "artifact_id": "analysis-001",
        "artifact_version": 3,
        "snapshot_digest": None,
        "reference_contract_version": "artifact-reference-v1",
    }
    values.update(overrides)
    return RealityGapArtifactReference(**values)


def read_reference(**overrides):
    values = {
        "artifact_reference": artifact(),
        "availability_status": AttachmentAvailabilityStatus.AVAILABLE,
        "read_contract_version": "canonical-read-v2",
    }
    values.update(overrides)
    return RealityGapAttachmentReadReferenceV2(**values)


class CanonicalReadBoundaryV2Tests(unittest.TestCase):
    def test_analysis_reference_preserves_version_only(self):
        value = read_reference()
        self.assertEqual(value.artifact_reference.artifact_version, 3)
        self.assertIsNone(value.artifact_reference.snapshot_digest)

    def test_classification_reference_preserves_digest_only(self):
        source = artifact(
            artifact_type=RealityGapArtifactType.CLASSIFICATION,
            artifact_id="classification-001",
            artifact_version=None,
            snapshot_digest=CLASSIFICATION_DIGEST,
        )
        value = read_reference(artifact_reference=source)
        self.assertIs(value.artifact_reference, source)
        self.assertIsNone(value.artifact_reference.artifact_version)
        self.assertEqual(
            value.artifact_reference.snapshot_digest, CLASSIFICATION_DIGEST
        )

    def test_metric_set_reference_preserves_digest_only(self):
        source = artifact(
            artifact_type=RealityGapArtifactType.METRIC_SET,
            artifact_id="metric-set-001",
            artifact_version=None,
            snapshot_digest=METRIC_SET_DIGEST,
        )
        value = read_reference(artifact_reference=source)
        self.assertIsNone(value.artifact_reference.artifact_version)
        self.assertEqual(value.artifact_reference.snapshot_digest, METRIC_SET_DIGEST)

    def test_dual_locators_are_preserved_without_conversion(self):
        source = artifact(snapshot_digest=CLASSIFICATION_DIGEST)
        value = read_reference(artifact_reference=source)
        self.assertEqual(value.artifact_reference.artifact_version, 3)
        self.assertEqual(
            value.artifact_reference.snapshot_digest, CLASSIFICATION_DIGEST
        )

    def test_unavailable_state(self):
        value = read_reference(availability_status="UNAVAILABLE")
        self.assertIs(
            value.availability_status, AttachmentAvailabilityStatus.UNAVAILABLE
        )

    def test_superseded_state(self):
        value = read_reference(availability_status="SUPERSEDED")
        self.assertIs(
            value.availability_status, AttachmentAvailabilityStatus.SUPERSEDED
        )

    def test_invalid_artifact_reference_is_rejected(self):
        with self.assertRaises(AttachmentReadV2ValidationError):
            read_reference(artifact_reference=None)
        with self.assertRaises(ArtifactReferenceValidationError):
            artifact(artifact_version=None, snapshot_digest=None)

    def test_read_contract_version_is_required(self):
        for value in (None, "", "  "):
            with self.subTest(value=value):
                with self.assertRaises(AttachmentReadV2ValidationError):
                    read_reference(read_contract_version=value)

    def test_contract_is_immutable(self):
        value = read_reference()
        with self.assertRaises(FrozenInstanceError):
            value.availability_status = AttachmentAvailabilityStatus.UNAVAILABLE

    def test_exposes_only_consumer_safe_fields(self):
        self.assertEqual(
            tuple(item.name for item in fields(RealityGapAttachmentReadReferenceV2)),
            (
                "artifact_reference",
                "availability_status",
                "read_contract_version",
            ),
        )
        forbidden = {
            "evidence",
            "candidates",
            "projections",
            "mappings",
            "evaluation",
        }
        self.assertTrue(forbidden.isdisjoint(read_reference().to_dict()))

    def test_serialization_round_trip_preserves_digest_and_none_version(self):
        value = read_reference(
            artifact_reference=artifact(
                artifact_type="CLASSIFICATION",
                artifact_id="classification-001",
                artifact_version=None,
                snapshot_digest=CLASSIFICATION_DIGEST,
            )
        )
        restored = RealityGapAttachmentReadReferenceV2.from_dict(value.to_dict())
        self.assertEqual(restored, value)
        self.assertIsNone(restored.artifact_reference.artifact_version)
        self.assertEqual(
            restored.artifact_reference.snapshot_digest, CLASSIFICATION_DIGEST
        )

    def test_canonical_json_is_deterministic(self):
        value = read_reference()
        first = value.canonical_json()
        second = RealityGapAttachmentReadReferenceV2.from_dict(
            json.loads(first)
        ).canonical_json()
        self.assertEqual(second, first)
        self.assertEqual(json.loads(first), value.to_dict())

    def test_unknown_serialized_fields_are_rejected(self):
        payload = read_reference().to_dict()
        payload["raw_evidence"] = []
        with self.assertRaises(AttachmentReadV2ValidationError):
            RealityGapAttachmentReadReferenceV2.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
