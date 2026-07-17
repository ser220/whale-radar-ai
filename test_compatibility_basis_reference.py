"""Focused tests for the immutable compatibility basis reference envelope."""

from dataclasses import FrozenInstanceError, fields
import json
import unittest

from app.intelligence.attachments import (
    CompatibilityDecisionBasisReferenceValidationError,
    RealityGapCompatibilityDecisionBasisReference,
)


BASIS_DIGEST = "sha256:" + ("e" * 64)


def reference(**overrides):
    values = {
        "basis_id": "compatibility-basis-001",
        "basis_version": 4,
        "basis_digest": None,
        "reference_contract_version": "basis-reference-v1",
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionBasisReference(**values)


class CompatibilityDecisionBasisReferenceTests(unittest.TestCase):
    def test_valid_version_only_reference(self):
        value = reference()
        self.assertEqual(value.basis_id, "compatibility-basis-001")
        self.assertEqual(value.basis_version, 4)
        self.assertIsNone(value.basis_digest)

    def test_version_and_digest_reference_preserves_both(self):
        value = reference(basis_digest=BASIS_DIGEST)
        self.assertEqual(value.basis_version, 4)
        self.assertEqual(value.basis_digest, BASIS_DIGEST)

    def test_invalid_digest_is_rejected(self):
        for value in (
            "",
            "sha256:ABC",
            "sha256:" + ("E" * 64),
            "sha256:" + ("e" * 63),
        ):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionBasisReferenceValidationError
                ):
                    reference(basis_digest=value)

    def test_invalid_version_and_boolean_are_rejected(self):
        for value in (True, False, 0, -1, 1.5, "1", None):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionBasisReferenceValidationError
                ):
                    reference(basis_version=value)

    def test_empty_identity_is_rejected(self):
        for value in (None, "", "  "):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionBasisReferenceValidationError
                ):
                    reference(basis_id=value)

    def test_reference_contract_version_is_required_and_validated(self):
        for value in (None, "", "  ", "bad version"):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionBasisReferenceValidationError
                ):
                    reference(reference_contract_version=value)

    def test_contract_is_immutable(self):
        value = reference()
        with self.assertRaises(FrozenInstanceError):
            value.basis_version = 5

    def test_exposes_identity_only_fields(self):
        self.assertEqual(
            tuple(
                item.name
                for item in fields(RealityGapCompatibilityDecisionBasisReference)
            ),
            (
                "basis_id",
                "basis_version",
                "basis_digest",
                "reference_contract_version",
            ),
        )
        forbidden = {
            "basis_type",
            "rule_code",
            "comparison_references",
            "evaluator_logic",
        }
        self.assertTrue(forbidden.isdisjoint(reference().to_dict()))

    def test_serialization_round_trip_is_deterministic(self):
        value = reference(basis_digest=BASIS_DIGEST)
        restored = RealityGapCompatibilityDecisionBasisReference.from_dict(
            value.to_dict()
        )
        self.assertEqual(restored, value)
        self.assertEqual(restored.canonical_json(), value.canonical_json())
        self.assertEqual(json.loads(value.canonical_json()), value.to_dict())

    def test_unknown_serialized_fields_are_rejected(self):
        payload = reference().to_dict()
        payload["rule_code"] = "FORBIDDEN"
        with self.assertRaises(CompatibilityDecisionBasisReferenceValidationError):
            RealityGapCompatibilityDecisionBasisReference.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
