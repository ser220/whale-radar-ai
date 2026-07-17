"""Focused tests for typed immutable compatibility association v2."""

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
import json
import unittest

from app.intelligence.attachments import (
    CompatibilityDecisionAssociationV2ValidationError,
    RealityGapArtifactReference,
    RealityGapArtifactType,
    RealityGapCompatibilityDecisionAssociationV2,
    RealityGapCompatibilityDecisionBasisReference,
    RealityGapCompatibilityDecisionReference,
)


UTC_TIME = datetime(2026, 7, 17, 10, 0, tzinfo=timezone.utc)
ATTACHMENT_DIGEST = "sha256:" + ("a" * 64)
DECISION_DIGEST = "sha256:" + ("d" * 64)
BASIS_DIGEST = "sha256:" + ("e" * 64)


def attachment_reference(**overrides):
    values = {
        "artifact_type": RealityGapArtifactType.ATTACHMENT,
        "artifact_id": "attachment-001",
        "artifact_version": 7,
        "snapshot_digest": None,
        "reference_contract_version": "artifact-reference-v1",
    }
    values.update(overrides)
    return RealityGapArtifactReference(**values)


def decision_reference(**overrides):
    values = {
        "decision_id": "compatibility-decision-001",
        "decision_version": 3,
        "decision_digest": DECISION_DIGEST,
        "reference_contract_version": "decision-reference-v1",
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionReference(**values)


def basis_reference(**overrides):
    values = {
        "basis_id": "compatibility-basis-001",
        "basis_version": 4,
        "basis_digest": BASIS_DIGEST,
        "reference_contract_version": "basis-reference-v1",
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionBasisReference(**values)


def association(**overrides):
    values = {
        "association_id": "association-v2-001",
        "attachment_reference": attachment_reference(),
        "decision_reference": decision_reference(),
        "basis_reference": basis_reference(),
        "associated_at": UTC_TIME,
        "association_contract_version": "compatibility-association-v2",
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionAssociationV2(**values)


class CompatibilityDecisionAssociationV2Tests(unittest.TestCase):
    def test_valid_association_uses_typed_references(self):
        value = association()
        self.assertIsInstance(
            value.decision_reference, RealityGapCompatibilityDecisionReference
        )
        self.assertIsInstance(
            value.basis_reference,
            RealityGapCompatibilityDecisionBasisReference,
        )
        self.assertEqual(value.attachment_reference.artifact_id, "attachment-001")

    def test_attachment_version_reference_is_preserved(self):
        value = association()
        self.assertEqual(value.attachment_reference.artifact_version, 7)
        self.assertIsNone(value.attachment_reference.snapshot_digest)

    def test_attachment_digest_reference_is_preserved(self):
        value = association(
            attachment_reference=attachment_reference(
                artifact_version=None,
                snapshot_digest=ATTACHMENT_DIGEST,
            )
        )
        self.assertIsNone(value.attachment_reference.artifact_version)
        self.assertEqual(
            value.attachment_reference.snapshot_digest, ATTACHMENT_DIGEST
        )

    def test_invalid_attachment_reference_is_rejected(self):
        with self.assertRaises(CompatibilityDecisionAssociationV2ValidationError):
            association(attachment_reference=None)
        with self.assertRaises(CompatibilityDecisionAssociationV2ValidationError):
            association(
                attachment_reference=attachment_reference(artifact_type="ANALYSIS")
            )

    def test_invalid_decision_reference_is_rejected(self):
        for value in (None, "compatibility-decision-001", {}):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionAssociationV2ValidationError
                ):
                    association(decision_reference=value)

    def test_invalid_basis_reference_is_rejected(self):
        for value in (None, "compatibility-basis-001", {}):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionAssociationV2ValidationError
                ):
                    association(basis_reference=value)

    def test_identity_timestamp_and_contract_version_validation(self):
        with self.assertRaises(CompatibilityDecisionAssociationV2ValidationError):
            association(association_id="")
        with self.assertRaises(CompatibilityDecisionAssociationV2ValidationError):
            association(associated_at=datetime(2026, 7, 17, 10, 0))
        for value in (None, "", "bad version"):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionAssociationV2ValidationError
                ):
                    association(association_contract_version=value)
        offset = timezone(timedelta(hours=2))
        self.assertEqual(
            association(
                associated_at=datetime(2026, 7, 17, 12, 0, tzinfo=offset)
            ).associated_at,
            UTC_TIME,
        )

    def test_contract_and_nested_references_are_immutable(self):
        value = association()
        with self.assertRaises(FrozenInstanceError):
            value.association_id = "replacement"
        with self.assertRaises(FrozenInstanceError):
            value.decision_reference.decision_version = 5

    def test_serialization_round_trip_preserves_typed_provenance(self):
        value = association(
            attachment_reference=attachment_reference(
                snapshot_digest=ATTACHMENT_DIGEST
            )
        )
        restored = RealityGapCompatibilityDecisionAssociationV2.from_dict(
            value.to_dict()
        )
        self.assertEqual(restored, value)
        self.assertIsInstance(
            restored.attachment_reference, RealityGapArtifactReference
        )
        self.assertIsInstance(
            restored.decision_reference,
            RealityGapCompatibilityDecisionReference,
        )
        self.assertIsInstance(
            restored.basis_reference,
            RealityGapCompatibilityDecisionBasisReference,
        )
        self.assertEqual(json.loads(value.canonical_json()), value.to_dict())
        self.assertEqual(restored.canonical_json(), value.canonical_json())

    def test_historical_provenance_and_public_shape(self):
        value = association()
        self.assertEqual(value.decision_reference.decision_version, 3)
        self.assertEqual(value.decision_reference.decision_digest, DECISION_DIGEST)
        self.assertEqual(value.basis_reference.basis_version, 4)
        self.assertEqual(value.basis_reference.basis_digest, BASIS_DIGEST)
        self.assertEqual(
            tuple(
                item.name
                for item in fields(RealityGapCompatibilityDecisionAssociationV2)
            ),
            (
                "association_id",
                "attachment_reference",
                "decision_reference",
                "basis_reference",
                "associated_at",
                "association_contract_version",
            ),
        )
        forbidden = {
            "compatibility_status",
            "decision_payload",
            "basis_payload",
            "evaluator_output",
        }
        self.assertTrue(forbidden.isdisjoint(value.to_dict()))

    def test_unknown_serialized_fields_are_rejected(self):
        payload = association().to_dict()
        payload["current_default"] = "forbidden"
        with self.assertRaises(CompatibilityDecisionAssociationV2ValidationError):
            RealityGapCompatibilityDecisionAssociationV2.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
