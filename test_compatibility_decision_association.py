"""Focused tests for immutable compatibility decision provenance association."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import json
import unittest

from app.intelligence.attachments import (
    CompatibilityDecisionAssociationValidationError,
    RealityGapArtifactReference,
    RealityGapArtifactType,
    RealityGapCompatibilityDecisionAssociation,
)


UTC_TIME = datetime(2026, 7, 17, 8, 0, tzinfo=timezone.utc)
ATTACHMENT_DIGEST = "sha256:" + ("c" * 64)


def attachment_reference(**overrides):
    values = {
        "artifact_type": RealityGapArtifactType.ATTACHMENT,
        "artifact_id": "attachment-001",
        "artifact_version": 7,
        "snapshot_digest": ATTACHMENT_DIGEST,
        "reference_contract_version": "artifact-reference-v1",
    }
    values.update(overrides)
    return RealityGapArtifactReference(**values)


def association(**overrides):
    values = {
        "association_id": "association-001",
        "attachment_reference": attachment_reference(),
        "compatibility_decision_reference": "compatibility-decision-001",
        "decision_basis_reference": "decision-basis-001",
        "associated_at": UTC_TIME,
        "association_contract_version": "compatibility-association-v1",
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionAssociation(**values)


class CompatibilityDecisionAssociationTests(unittest.TestCase):
    def test_valid_association_preserves_independent_identities(self):
        value = association()
        self.assertEqual(value.association_id, "association-001")
        self.assertEqual(
            value.attachment_reference.artifact_id, "attachment-001"
        )
        self.assertEqual(
            value.compatibility_decision_reference,
            "compatibility-decision-001",
        )
        self.assertEqual(value.decision_basis_reference, "decision-basis-001")

    def test_attachment_artifact_type_is_additive_and_canonical(self):
        existing = (
            RealityGapArtifactType.ANALYSIS.value,
            RealityGapArtifactType.CLASSIFICATION.value,
            RealityGapArtifactType.METRIC_SET.value,
        )
        self.assertEqual(existing, ("ANALYSIS", "CLASSIFICATION", "METRIC_SET"))
        self.assertEqual(RealityGapArtifactType.ATTACHMENT.value, "ATTACHMENT")
        restored = RealityGapArtifactReference.from_dict(
            attachment_reference().to_dict()
        )
        self.assertIs(restored.artifact_type, RealityGapArtifactType.ATTACHMENT)

    def test_invalid_attachment_reference_is_rejected(self):
        with self.assertRaises(CompatibilityDecisionAssociationValidationError):
            association(attachment_reference=None)
        with self.assertRaises(CompatibilityDecisionAssociationValidationError):
            association(
                attachment_reference=attachment_reference(artifact_type="ANALYSIS")
            )

    def test_missing_decision_reference_is_rejected(self):
        for value in (None, "", "  "):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionAssociationValidationError
                ):
                    association(compatibility_decision_reference=value)

    def test_missing_basis_reference_is_rejected(self):
        for value in (None, "", "  "):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionAssociationValidationError
                ):
                    association(decision_basis_reference=value)

    def test_identity_and_contract_version_validation(self):
        with self.assertRaises(CompatibilityDecisionAssociationValidationError):
            association(association_id="")
        for value in (None, "", "bad version"):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionAssociationValidationError
                ):
                    association(association_contract_version=value)
        with self.assertRaises(CompatibilityDecisionAssociationValidationError):
            association(decision_basis_reference="association-001")

    def test_timestamp_validation_and_utc_normalization(self):
        with self.assertRaises(CompatibilityDecisionAssociationValidationError):
            association(associated_at=datetime(2026, 7, 17, 8, 0))
        offset = timezone(timedelta(hours=3))
        value = association(
            associated_at=datetime(2026, 7, 17, 11, 0, tzinfo=offset)
        )
        self.assertEqual(value.associated_at, UTC_TIME)
        self.assertEqual(value.associated_at.tzinfo, timezone.utc)

    def test_contract_is_immutable(self):
        value = association()
        with self.assertRaises(FrozenInstanceError):
            value.decision_basis_reference = "replacement"
        with self.assertRaises(FrozenInstanceError):
            value.attachment_reference = attachment_reference(artifact_version=8)

    def test_serialization_round_trip(self):
        value = association()
        restored = RealityGapCompatibilityDecisionAssociation.from_dict(
            value.to_dict()
        )
        self.assertEqual(restored, value)
        self.assertIsInstance(
            restored.attachment_reference, RealityGapArtifactReference
        )
        self.assertEqual(json.loads(value.canonical_json()), value.to_dict())
        self.assertEqual(restored.canonical_json(), value.canonical_json())

    def test_historical_reference_preservation_without_conversion(self):
        version_only = association(
            attachment_reference=attachment_reference(snapshot_digest=None)
        )
        restored_version = RealityGapCompatibilityDecisionAssociation.from_dict(
            version_only.to_dict()
        )
        self.assertEqual(restored_version.attachment_reference.artifact_version, 7)
        self.assertIsNone(restored_version.attachment_reference.snapshot_digest)

        digest_only = association(
            attachment_reference=attachment_reference(artifact_version=None)
        )
        restored_digest = RealityGapCompatibilityDecisionAssociation.from_dict(
            digest_only.to_dict()
        )
        self.assertIsNone(restored_digest.attachment_reference.artifact_version)
        self.assertEqual(
            restored_digest.attachment_reference.snapshot_digest,
            ATTACHMENT_DIGEST,
        )

    def test_unknown_serialized_field_is_rejected(self):
        payload = association().to_dict()
        payload["current_default"] = "forbidden"
        with self.assertRaises(CompatibilityDecisionAssociationValidationError):
            RealityGapCompatibilityDecisionAssociation.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
