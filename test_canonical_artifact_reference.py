"""Focused tests for the lossless canonical artifact reference contract."""

from dataclasses import FrozenInstanceError, fields
import json
import unittest

from app.intelligence.attachments import (
    ArtifactReferenceValidationError,
    RealityGapArtifactReference,
    RealityGapArtifactType,
)


CLASSIFICATION_DIGEST = "sha256:" + ("a" * 64)
METRIC_SET_DIGEST = "sha256:" + ("b" * 64)


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


class RealityGapArtifactReferenceTests(unittest.TestCase):
    def test_analysis_reference_preserves_version_without_fake_digest(self):
        value = reference()
        self.assertIs(value.artifact_type, RealityGapArtifactType.ANALYSIS)
        self.assertEqual(value.artifact_version, 3)
        self.assertIsNone(value.snapshot_digest)

    def test_classification_reference_preserves_digest_without_fake_version(self):
        value = reference(
            artifact_type=RealityGapArtifactType.CLASSIFICATION,
            artifact_id="classification-001",
            artifact_version=None,
            snapshot_digest=CLASSIFICATION_DIGEST,
        )
        self.assertIsNone(value.artifact_version)
        self.assertEqual(value.snapshot_digest, CLASSIFICATION_DIGEST)

    def test_metric_set_reference_preserves_digest_without_fake_version(self):
        value = reference(
            artifact_type=RealityGapArtifactType.METRIC_SET,
            artifact_id="metric-set-001",
            artifact_version=None,
            snapshot_digest=METRIC_SET_DIGEST,
        )
        self.assertIsNone(value.artifact_version)
        self.assertEqual(value.snapshot_digest, METRIC_SET_DIGEST)

    def test_version_and_digest_may_coexist_without_conversion(self):
        value = reference(snapshot_digest=CLASSIFICATION_DIGEST)
        self.assertEqual(value.artifact_version, 3)
        self.assertEqual(value.snapshot_digest, CLASSIFICATION_DIGEST)

    def test_invalid_digest_is_rejected(self):
        invalid = (
            "",
            "a" * 64,
            "sha256:" + ("A" * 64),
            "sha256:" + ("g" * 64),
            "sha256:" + ("a" * 63),
        )
        for digest in invalid:
            with self.subTest(digest=digest):
                with self.assertRaises(ArtifactReferenceValidationError):
                    reference(snapshot_digest=digest)

    def test_missing_historical_locator_is_rejected(self):
        with self.assertRaises(ArtifactReferenceValidationError) as caught:
            reference(artifact_version=None, snapshot_digest=None)
        self.assertEqual(caught.exception.field_name, "historical_locator")

    def test_identity_and_version_validation(self):
        for overrides in (
            {"artifact_id": ""},
            {"artifact_version": 0},
            {"artifact_version": True},
            {"reference_contract_version": ""},
            {"reference_contract_version": "bad version"},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ArtifactReferenceValidationError):
                    reference(**overrides)

    def test_unknown_artifact_type_is_rejected(self):
        with self.assertRaises(ArtifactReferenceValidationError):
            reference(artifact_type="EVIDENCE")

    def test_contract_is_immutable(self):
        value = reference()
        with self.assertRaises(FrozenInstanceError):
            value.artifact_version = 4

    def test_exact_public_fields(self):
        self.assertEqual(
            tuple(item.name for item in fields(RealityGapArtifactReference)),
            (
                "artifact_type",
                "artifact_id",
                "artifact_version",
                "snapshot_digest",
                "reference_contract_version",
            ),
        )

    def test_serialization_round_trip_preserves_locator_types(self):
        values = (
            reference(),
            reference(
                artifact_type="CLASSIFICATION",
                artifact_id="classification-001",
                artifact_version=None,
                snapshot_digest=CLASSIFICATION_DIGEST,
            ),
            reference(snapshot_digest=METRIC_SET_DIGEST),
        )
        for value in values:
            with self.subTest(value=value):
                restored = RealityGapArtifactReference.from_dict(value.to_dict())
                self.assertEqual(restored, value)
                self.assertIsInstance(restored.artifact_type, RealityGapArtifactType)

    def test_canonical_json_is_deterministic_and_explicitly_preserves_none(self):
        value = reference()
        first = value.canonical_json()
        second = RealityGapArtifactReference.from_dict(
            json.loads(first)
        ).canonical_json()
        self.assertEqual(second, first)
        self.assertIsNone(json.loads(first)["snapshot_digest"])

    def test_unknown_or_missing_serialized_fields_are_rejected(self):
        valid = reference().to_dict()
        for payload in (
            dict(valid, current_default="forbidden"),
            {key: item for key, item in valid.items() if key != "artifact_id"},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ArtifactReferenceValidationError):
                    RealityGapArtifactReference.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
