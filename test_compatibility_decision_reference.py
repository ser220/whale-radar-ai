"""Focused tests for the immutable compatibility decision reference envelope."""

from dataclasses import FrozenInstanceError, fields
import json
import unittest

from app.intelligence.attachments import (
    CompatibilityDecisionReferenceValidationError,
    RealityGapCompatibilityDecisionReference,
)


DECISION_DIGEST = "sha256:" + ("d" * 64)


def reference(**overrides):
    values = {
        "decision_id": "compatibility-decision-001",
        "decision_version": 3,
        "decision_digest": None,
        "reference_contract_version": "decision-reference-v1",
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionReference(**values)


class CompatibilityDecisionReferenceTests(unittest.TestCase):
    def test_valid_version_only_reference(self):
        value = reference()
        self.assertEqual(value.decision_id, "compatibility-decision-001")
        self.assertEqual(value.decision_version, 3)
        self.assertIsNone(value.decision_digest)

    def test_version_and_digest_reference_preserves_both(self):
        value = reference(decision_digest=DECISION_DIGEST)
        self.assertEqual(value.decision_version, 3)
        self.assertEqual(value.decision_digest, DECISION_DIGEST)

    def test_invalid_digest_is_rejected(self):
        for value in (
            "",
            "sha256:ABC",
            "sha256:" + ("D" * 64),
            "sha256:" + ("d" * 63),
        ):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionReferenceValidationError
                ):
                    reference(decision_digest=value)

    def test_invalid_version_and_boolean_are_rejected(self):
        for value in (True, False, 0, -1, 1.5, "1", None):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionReferenceValidationError
                ):
                    reference(decision_version=value)

    def test_empty_identity_is_rejected(self):
        for value in (None, "", "  "):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionReferenceValidationError
                ):
                    reference(decision_id=value)

    def test_reference_contract_version_is_required_and_validated(self):
        for value in (None, "", "  ", "bad version"):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionReferenceValidationError
                ):
                    reference(reference_contract_version=value)

    def test_contract_is_immutable(self):
        value = reference()
        with self.assertRaises(FrozenInstanceError):
            value.decision_version = 4

    def test_exposes_identity_only_fields(self):
        self.assertEqual(
            tuple(
                item.name
                for item in fields(RealityGapCompatibilityDecisionReference)
            ),
            (
                "decision_id",
                "decision_version",
                "decision_digest",
                "reference_contract_version",
            ),
        )
        forbidden = {
            "compatibility_status",
            "decision_basis",
            "evaluator_output",
            "policy_logic",
        }
        self.assertTrue(forbidden.isdisjoint(reference().to_dict()))

    def test_serialization_round_trip_is_deterministic(self):
        value = reference(decision_digest=DECISION_DIGEST)
        restored = RealityGapCompatibilityDecisionReference.from_dict(
            value.to_dict()
        )
        self.assertEqual(restored, value)
        self.assertEqual(restored.canonical_json(), value.canonical_json())
        self.assertEqual(json.loads(value.canonical_json()), value.to_dict())

    def test_unknown_serialized_fields_are_rejected(self):
        payload = reference().to_dict()
        payload["compatibility_status"] = "COMPATIBLE"
        with self.assertRaises(CompatibilityDecisionReferenceValidationError):
            RealityGapCompatibilityDecisionReference.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
