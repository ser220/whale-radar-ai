"""Focused tests for immutable compatibility decision basis provenance."""

from dataclasses import FrozenInstanceError
import json
import unittest

from app.intelligence.attachments import (
    CompatibilityDecisionBasisType,
    CompatibilityDecisionBasisValidationError,
    RealityGapArtifactReference,
    RealityGapArtifactType,
    RealityGapCompatibilityDecisionBasis,
)


DIGEST_A = "sha256:" + ("a" * 64)
DIGEST_B = "sha256:" + ("b" * 64)


def reference(**overrides):
    values = {
        "artifact_type": RealityGapArtifactType.ANALYSIS,
        "artifact_id": "analysis-001",
        "artifact_version": 3,
        "snapshot_digest": None,
        "reference_contract_version": "artifact-reference-v1",
    }
    values.update(overrides)
    return RealityGapArtifactReference(**values)


def basis(**overrides):
    values = {
        "basis_type": CompatibilityDecisionBasisType.VERSION_RULE,
        "policy_version": "attachment-compatibility-v1",
        "rule_code": "PATCH_COMPATIBLE",
        "reference_snapshot": {
            "current": reference(artifact_id="analysis-current", artifact_version=4),
            "historical": reference(),
        },
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionBasis(**values)


class CompatibilityDecisionBasisTests(unittest.TestCase):
    def test_version_rule_basis_preserves_versions_without_digests(self):
        value = basis()
        self.assertIs(value.basis_type, CompatibilityDecisionBasisType.VERSION_RULE)
        self.assertEqual(value.reference_snapshot["historical"].artifact_version, 3)
        self.assertIsNone(
            value.reference_snapshot["historical"].snapshot_digest
        )

    def test_digest_rule_basis_preserves_digest_without_fake_version(self):
        value = basis(
            basis_type="DIGEST_RULE",
            rule_code="DIGEST_MATCH",
            reference_snapshot={
                "classification": reference(
                    artifact_type="CLASSIFICATION",
                    artifact_id="classification-001",
                    artifact_version=None,
                    snapshot_digest=DIGEST_A,
                ),
                "metric_set": reference(
                    artifact_type="METRIC_SET",
                    artifact_id="metric-set-001",
                    artifact_version=None,
                    snapshot_digest=DIGEST_B,
                ),
            },
        )
        self.assertIs(value.basis_type, CompatibilityDecisionBasisType.DIGEST_RULE)
        self.assertIsNone(
            value.reference_snapshot["classification"].artifact_version
        )
        self.assertEqual(
            value.reference_snapshot["classification"].snapshot_digest,
            DIGEST_A,
        )

    def test_manual_review_basis_is_explanation_not_status(self):
        value = basis(
            basis_type="MANUAL_REVIEW",
            rule_code="HUMAN_REVIEW_REQUIRED",
            reference_snapshot={"historical": reference()},
        )
        self.assertIs(
            value.basis_type, CompatibilityDecisionBasisType.MANUAL_REVIEW
        )
        self.assertNotIn("compatibility_status", value.to_dict())

    def test_empty_rule_and_policy_are_rejected(self):
        for override in ({"rule_code": "  "}, {"policy_version": ""}):
            with self.subTest(override=override):
                with self.assertRaises(CompatibilityDecisionBasisValidationError):
                    basis(**override)

    def test_unknown_basis_type_is_rejected(self):
        with self.assertRaises(CompatibilityDecisionBasisValidationError):
            basis(basis_type="AUTOMATIC_GUESS")

    def test_invalid_reference_is_rejected(self):
        with self.assertRaises(CompatibilityDecisionBasisValidationError):
            basis(reference_snapshot={"historical": {"artifact_id": "bad"}})
        with self.assertRaises(CompatibilityDecisionBasisValidationError):
            basis(reference_snapshot={})

    def test_contract_and_snapshot_are_immutable(self):
        source = {"historical": reference()}
        value = basis(reference_snapshot=source)
        source["historical"] = reference(artifact_id="replacement")
        self.assertEqual(
            value.reference_snapshot["historical"].artifact_id, "analysis-001"
        )
        with self.assertRaises(TypeError):
            value.reference_snapshot["new"] = reference()
        with self.assertRaises(FrozenInstanceError):
            value.rule_code = "OTHER"

    def test_serialization_round_trip_preserves_reference_types(self):
        value = basis(
            basis_type="DIGEST_RULE",
            rule_code="DIGEST_MATCH",
            reference_snapshot={
                "historical": reference(
                    artifact_type="CLASSIFICATION",
                    artifact_version=None,
                    snapshot_digest=DIGEST_A,
                )
            },
        )
        restored = RealityGapCompatibilityDecisionBasis.from_dict(value.to_dict())
        self.assertEqual(restored, value)
        self.assertIsInstance(
            restored.reference_snapshot["historical"],
            RealityGapArtifactReference,
        )

    def test_canonical_json_is_deterministic(self):
        value = basis()
        encoded = value.canonical_json()
        restored = RealityGapCompatibilityDecisionBasis.from_dict(
            json.loads(encoded)
        )
        self.assertEqual(restored.canonical_json(), encoded)
        self.assertEqual(json.loads(encoded), value.to_dict())

    def test_unknown_serialized_fields_are_rejected(self):
        payload = basis().to_dict()
        payload["compatibility_status"] = "COMPATIBLE"
        with self.assertRaises(CompatibilityDecisionBasisValidationError):
            RealityGapCompatibilityDecisionBasis.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
