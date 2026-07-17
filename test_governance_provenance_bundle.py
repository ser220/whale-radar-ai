"""Focused tests for the immutable governance provenance bundle."""

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
import json
import unittest

from app.intelligence.attachments import (
    AttachmentCompatibilityStatus,
    AttachmentReadReference,
    CompatibilityDecisionBasisType,
    GovernanceProvenanceBundleValidationError,
    RealityGapArtifactReference,
    RealityGapArtifactType,
    RealityGapAttachmentCompatibilityDecision,
    RealityGapCompatibilityDecisionAssociationV2,
    RealityGapCompatibilityDecisionBasis,
    RealityGapCompatibilityDecisionBasisRecordEnvelope,
    RealityGapCompatibilityDecisionBasisReference,
    RealityGapCompatibilityDecisionRecordEnvelope,
    RealityGapCompatibilityDecisionReference,
    RealityGapGovernanceProvenanceBundle,
)


UTC_TIME = datetime(2026, 7, 17, 18, 0, tzinfo=timezone.utc)
ATTACHMENT_DIGEST = "sha256:" + ("a" * 64)
DECISION_DIGEST = "sha256:" + ("d" * 64)
BASIS_DIGEST = "sha256:" + ("b" * 64)
SNAPSHOT_DIGEST = "sha256:" + ("c" * 64)


def artifact_reference(**overrides):
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


def decision_payload():
    return RealityGapAttachmentCompatibilityDecision(
        attachment_reference=AttachmentReadReference("attachment-read-001", 7),
        analysis_reference=AttachmentReadReference("analysis-001", 3),
        classification_reference=AttachmentReadReference(
            "classification-001", 2
        ),
        metrics_reference=AttachmentReadReference("metrics-001", 5),
        compatibility_status=AttachmentCompatibilityStatus.COMPATIBLE,
        policy_version="attachment-compatibility-v1",
        evaluated_at=UTC_TIME,
    )


def basis_payload():
    return RealityGapCompatibilityDecisionBasis(
        basis_type=CompatibilityDecisionBasisType.DIGEST_RULE,
        policy_version="attachment-compatibility-v1",
        rule_code="DIGEST_MATCH",
        reference_snapshot={
            "classification": artifact_reference(
                artifact_type=RealityGapArtifactType.CLASSIFICATION,
                artifact_id="classification-001",
                artifact_version=None,
                snapshot_digest=SNAPSHOT_DIGEST,
            )
        },
    )


def decision_record(**overrides):
    values = {
        "decision_reference": decision_reference(),
        "decision_payload": decision_payload(),
        "envelope_version": "decision-record-envelope-v1",
        "created_at": UTC_TIME,
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionRecordEnvelope(**values)


def basis_record(**overrides):
    values = {
        "basis_reference": basis_reference(),
        "basis_payload": basis_payload(),
        "envelope_version": "basis-record-envelope-v1",
        "created_at": UTC_TIME,
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionBasisRecordEnvelope(**values)


def association(**overrides):
    values = {
        "association_id": "association-v2-001",
        "attachment_reference": artifact_reference(),
        "decision_reference": decision_reference(),
        "basis_reference": basis_reference(),
        "associated_at": UTC_TIME,
        "association_contract_version": "compatibility-association-v2",
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionAssociationV2(**values)


def bundle(**overrides):
    values = {
        "bundle_id": "governance-bundle-001",
        "attachment_reference": artifact_reference(),
        "decision_record": decision_record(),
        "basis_record": basis_record(),
        "association": association(),
        "bundle_version": "governance-provenance-bundle-v1",
        "created_at": UTC_TIME,
    }
    values.update(overrides)
    return RealityGapGovernanceProvenanceBundle(**values)


class GovernanceProvenanceBundleTests(unittest.TestCase):
    def test_valid_bundle_composes_all_typed_records(self):
        value = bundle()
        self.assertIsInstance(
            value.decision_record,
            RealityGapCompatibilityDecisionRecordEnvelope,
        )
        self.assertIsInstance(
            value.basis_record,
            RealityGapCompatibilityDecisionBasisRecordEnvelope,
        )
        self.assertIsInstance(
            value.association,
            RealityGapCompatibilityDecisionAssociationV2,
        )

    def test_version_only_attachment_locator_is_preserved(self):
        value = bundle()
        self.assertEqual(value.attachment_reference.artifact_version, 7)
        self.assertIsNone(value.attachment_reference.snapshot_digest)

    def test_digest_only_attachment_locator_is_preserved(self):
        value = bundle(
            attachment_reference=artifact_reference(
                artifact_version=None,
                snapshot_digest=ATTACHMENT_DIGEST,
            )
        )
        self.assertIsNone(value.attachment_reference.artifact_version)
        self.assertEqual(
            value.attachment_reference.snapshot_digest, ATTACHMENT_DIGEST
        )

    def test_dual_attachment_locators_are_preserved(self):
        value = bundle(
            attachment_reference=artifact_reference(
                snapshot_digest=ATTACHMENT_DIGEST
            )
        )
        self.assertEqual(value.attachment_reference.artifact_version, 7)
        self.assertEqual(
            value.attachment_reference.snapshot_digest, ATTACHMENT_DIGEST
        )

    def test_invalid_nested_contract_types_are_rejected(self):
        invalid_fields = {
            "attachment_reference": None,
            "decision_record": {},
            "basis_record": "basis-record",
            "association": None,
        }
        for field_name, invalid_value in invalid_fields.items():
            with self.subTest(field_name=field_name):
                with self.assertRaises(
                    GovernanceProvenanceBundleValidationError
                ):
                    bundle(**{field_name: invalid_value})

    def test_non_attachment_root_reference_is_rejected(self):
        with self.assertRaises(GovernanceProvenanceBundleValidationError):
            bundle(
                attachment_reference=artifact_reference(
                    artifact_type=RealityGapArtifactType.ANALYSIS
                )
            )

    def test_identity_timestamp_and_version_validation(self):
        for value in (None, "", "  "):
            with self.subTest(bundle_id=value):
                with self.assertRaises(
                    GovernanceProvenanceBundleValidationError
                ):
                    bundle(bundle_id=value)
        for value in (None, "", "bad version"):
            with self.subTest(bundle_version=value):
                with self.assertRaises(
                    GovernanceProvenanceBundleValidationError
                ):
                    bundle(bundle_version=value)
        with self.assertRaises(GovernanceProvenanceBundleValidationError):
            bundle(created_at=datetime(2026, 7, 17, 18, 0))
        offset = timezone(timedelta(hours=2))
        normalized = bundle(
            created_at=datetime(2026, 7, 17, 20, 0, tzinfo=offset)
        )
        self.assertEqual(normalized.created_at, UTC_TIME)

    def test_bundle_and_nested_contracts_are_immutable(self):
        value = bundle()
        with self.assertRaises(FrozenInstanceError):
            value.bundle_version = "v2"
        with self.assertRaises(FrozenInstanceError):
            value.attachment_reference.artifact_version = 8
        with self.assertRaises(FrozenInstanceError):
            value.decision_record.envelope_version = "v2"
        with self.assertRaises(TypeError):
            value.basis_record.basis_payload.reference_snapshot["new"] = (
                artifact_reference()
            )

    def test_serialization_round_trip_is_deterministic_and_lossless(self):
        value = bundle(
            attachment_reference=artifact_reference(
                snapshot_digest=ATTACHMENT_DIGEST
            )
        )
        restored = RealityGapGovernanceProvenanceBundle.from_dict(
            value.to_dict()
        )
        self.assertEqual(restored, value)
        self.assertEqual(restored.canonical_json(), value.canonical_json())
        self.assertEqual(json.loads(value.canonical_json()), value.to_dict())

    def test_bundle_does_not_compare_nested_identifiers_or_locators(self):
        value = bundle(
            attachment_reference=artifact_reference(
                artifact_id="bundle-attachment",
                artifact_version=11,
            ),
            decision_record=decision_record(
                decision_reference=decision_reference(
                    decision_id="record-decision", decision_version=12
                )
            ),
            basis_record=basis_record(
                basis_reference=basis_reference(
                    basis_id="record-basis", basis_version=13
                )
            ),
            association=association(
                attachment_reference=artifact_reference(
                    artifact_id="association-attachment",
                    artifact_version=14,
                ),
                decision_reference=decision_reference(
                    decision_id="association-decision", decision_version=15
                ),
                basis_reference=basis_reference(
                    basis_id="association-basis", basis_version=16
                ),
            ),
        )
        self.assertEqual(
            value.attachment_reference.artifact_id, "bundle-attachment"
        )
        self.assertEqual(
            value.association.attachment_reference.artifact_id,
            "association-attachment",
        )

    def test_public_shape_contains_no_runtime_or_semantic_validator_fields(self):
        self.assertEqual(
            tuple(
                item.name
                for item in fields(RealityGapGovernanceProvenanceBundle)
            ),
            (
                "bundle_id",
                "attachment_reference",
                "decision_record",
                "basis_record",
                "association",
                "bundle_version",
                "created_at",
            ),
        )
        forbidden = {
            "compatibility_evaluator",
            "resolved_reference",
            "calculated_digest",
            "semantic_validation_result",
            "current_default",
        }
        self.assertTrue(forbidden.isdisjoint(bundle().to_dict()))

    def test_unknown_or_incomplete_serialized_fields_are_rejected(self):
        unknown = bundle().to_dict()
        unknown["resolver"] = "forbidden"
        with self.assertRaises(GovernanceProvenanceBundleValidationError):
            RealityGapGovernanceProvenanceBundle.from_dict(unknown)

        incomplete = bundle().to_dict()
        del incomplete["basis_record"]
        with self.assertRaises(GovernanceProvenanceBundleValidationError):
            RealityGapGovernanceProvenanceBundle.from_dict(incomplete)

    def test_invalid_nested_serialized_value_is_rejected(self):
        payload = bundle().to_dict()
        payload["association"] = {"association_id": "partial"}
        with self.assertRaises(GovernanceProvenanceBundleValidationError):
            RealityGapGovernanceProvenanceBundle.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
