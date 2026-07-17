"""Focused tests for the immutable compatibility basis record envelope."""

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
import json
import unittest

from app.intelligence.attachments import (
    CompatibilityDecisionBasisRecordEnvelopeValidationError,
    CompatibilityDecisionBasisType,
    RealityGapArtifactReference,
    RealityGapArtifactType,
    RealityGapCompatibilityDecisionBasis,
    RealityGapCompatibilityDecisionBasisRecordEnvelope,
    RealityGapCompatibilityDecisionBasisReference,
)


UTC_TIME = datetime(2026, 7, 17, 16, 0, tzinfo=timezone.utc)
BASIS_DIGEST = "sha256:" + ("b" * 64)
SNAPSHOT_DIGEST = "sha256:" + ("a" * 64)


def basis_reference(**overrides):
    values = {
        "basis_id": "compatibility-basis-001",
        "basis_version": 4,
        "basis_digest": None,
        "reference_contract_version": "basis-reference-v1",
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionBasisReference(**values)


def artifact_reference(**overrides):
    values = {
        "artifact_type": RealityGapArtifactType.ANALYSIS,
        "artifact_id": "analysis-001",
        "artifact_version": 3,
        "snapshot_digest": None,
        "reference_contract_version": "artifact-reference-v1",
    }
    values.update(overrides)
    return RealityGapArtifactReference(**values)


def basis_payload(**overrides):
    values = {
        "basis_type": CompatibilityDecisionBasisType.VERSION_RULE,
        "policy_version": "attachment-compatibility-v1",
        "rule_code": "PATCH_COMPATIBLE",
        "reference_snapshot": {
            "current": artifact_reference(
                artifact_id="analysis-current", artifact_version=4
            ),
            "historical": artifact_reference(),
        },
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionBasis(**values)


def envelope(**overrides):
    values = {
        "basis_reference": basis_reference(),
        "basis_payload": basis_payload(),
        "envelope_version": "basis-record-envelope-v1",
        "created_at": UTC_TIME,
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionBasisRecordEnvelope(**values)


class CompatibilityDecisionBasisRecordEnvelopeTests(unittest.TestCase):
    def test_valid_basis_record_envelope_binds_reference_and_payload(self):
        value = envelope()
        self.assertIsInstance(
            value.basis_reference,
            RealityGapCompatibilityDecisionBasisReference,
        )
        self.assertIsInstance(
            value.basis_payload, RealityGapCompatibilityDecisionBasis
        )

    def test_version_only_basis_reference_is_preserved(self):
        value = envelope(basis_reference=basis_reference())
        self.assertEqual(value.basis_reference.basis_version, 4)
        self.assertIsNone(value.basis_reference.basis_digest)

    def test_version_and_digest_reference_are_both_preserved(self):
        value = envelope(
            basis_reference=basis_reference(basis_digest=BASIS_DIGEST)
        )
        self.assertEqual(value.basis_reference.basis_version, 4)
        self.assertEqual(value.basis_reference.basis_digest, BASIS_DIGEST)

    def test_invalid_reference_is_rejected(self):
        for value in (None, {}, "basis-001"):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionBasisRecordEnvelopeValidationError
                ):
                    envelope(basis_reference=value)

    def test_invalid_payload_is_rejected(self):
        for value in (None, {}, "VERSION_RULE"):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionBasisRecordEnvelopeValidationError
                ):
                    envelope(basis_payload=value)

    def test_created_at_requires_aware_time_and_normalizes_utc(self):
        with self.assertRaises(
            CompatibilityDecisionBasisRecordEnvelopeValidationError
        ):
            envelope(created_at=datetime(2026, 7, 17, 16, 0))

        offset = timezone(timedelta(hours=2))
        value = envelope(
            created_at=datetime(2026, 7, 17, 18, 0, tzinfo=offset)
        )
        self.assertEqual(value.created_at, UTC_TIME)
        self.assertEqual(value.created_at.tzinfo, timezone.utc)

    def test_envelope_version_is_required_and_validated(self):
        for value in (None, "", "  ", "bad version"):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionBasisRecordEnvelopeValidationError
                ):
                    envelope(envelope_version=value)

    def test_envelope_and_nested_records_are_immutable(self):
        source_snapshot = {"historical": artifact_reference()}
        value = envelope(
            basis_payload=basis_payload(reference_snapshot=source_snapshot)
        )
        source_snapshot["historical"] = artifact_reference(
            artifact_id="replacement"
        )
        self.assertEqual(
            value.basis_payload.reference_snapshot["historical"].artifact_id,
            "analysis-001",
        )
        with self.assertRaises(FrozenInstanceError):
            value.envelope_version = "v2"
        with self.assertRaises(FrozenInstanceError):
            value.basis_reference.basis_version = 5
        with self.assertRaises(TypeError):
            value.basis_payload.reference_snapshot["new"] = artifact_reference()

    def test_serialization_round_trip_is_deterministic(self):
        value = envelope(
            basis_reference=basis_reference(basis_digest=BASIS_DIGEST),
            basis_payload=basis_payload(
                basis_type=CompatibilityDecisionBasisType.DIGEST_RULE,
                rule_code="DIGEST_MATCH",
                reference_snapshot={
                    "classification": artifact_reference(
                        artifact_type=RealityGapArtifactType.CLASSIFICATION,
                        artifact_id="classification-001",
                        artifact_version=None,
                        snapshot_digest=SNAPSHOT_DIGEST,
                    )
                },
            ),
        )
        restored = RealityGapCompatibilityDecisionBasisRecordEnvelope.from_dict(
            value.to_dict()
        )
        self.assertEqual(restored, value)
        self.assertEqual(restored.canonical_json(), value.canonical_json())
        self.assertEqual(json.loads(value.canonical_json()), value.to_dict())

    def test_historical_identity_and_complete_payload_are_preserved(self):
        value = envelope(
            basis_reference=basis_reference(
                basis_id="historical-basis-009",
                basis_version=9,
                basis_digest=BASIS_DIGEST,
            )
        )
        restored = RealityGapCompatibilityDecisionBasisRecordEnvelope.from_dict(
            value.to_dict()
        )
        self.assertEqual(restored.basis_reference, value.basis_reference)
        self.assertEqual(restored.basis_payload, value.basis_payload)
        self.assertEqual(
            restored.basis_payload.to_dict(), value.basis_payload.to_dict()
        )

    def test_contract_exposes_only_record_envelope_fields(self):
        self.assertEqual(
            tuple(
                item.name
                for item in fields(
                    RealityGapCompatibilityDecisionBasisRecordEnvelope
                )
            ),
            (
                "basis_reference",
                "basis_payload",
                "envelope_version",
                "created_at",
            ),
        )
        forbidden = {
            "calculated_digest",
            "compatibility_evaluator",
            "resolved_reference",
            "current_default",
        }
        self.assertTrue(forbidden.isdisjoint(envelope().to_dict()))

    def test_invalid_nested_serialized_values_and_unknown_fields_are_rejected(self):
        invalid_reference = envelope().to_dict()
        invalid_reference["basis_reference"] = {"basis_id": "partial"}
        with self.assertRaises(
            CompatibilityDecisionBasisRecordEnvelopeValidationError
        ):
            RealityGapCompatibilityDecisionBasisRecordEnvelope.from_dict(
                invalid_reference
            )

        invalid_payload = envelope().to_dict()
        invalid_payload["basis_payload"] = {"rule_code": "partial"}
        with self.assertRaises(
            CompatibilityDecisionBasisRecordEnvelopeValidationError
        ):
            RealityGapCompatibilityDecisionBasisRecordEnvelope.from_dict(
                invalid_payload
            )

        unknown = envelope().to_dict()
        unknown["resolver"] = "forbidden"
        with self.assertRaises(
            CompatibilityDecisionBasisRecordEnvelopeValidationError
        ):
            RealityGapCompatibilityDecisionBasisRecordEnvelope.from_dict(unknown)


if __name__ == "__main__":
    unittest.main()
