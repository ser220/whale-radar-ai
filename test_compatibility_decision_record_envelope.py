"""Focused tests for the immutable compatibility decision record envelope."""

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
import json
import unittest

from app.intelligence.attachments import (
    AttachmentCompatibilityStatus,
    AttachmentReadReference,
    CompatibilityDecisionRecordEnvelopeValidationError,
    RealityGapAttachmentCompatibilityDecision,
    RealityGapCompatibilityDecisionRecordEnvelope,
    RealityGapCompatibilityDecisionReference,
)


UTC_TIME = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
DECISION_DIGEST = "sha256:" + ("d" * 64)


def decision_reference(**overrides):
    values = {
        "decision_id": "compatibility-decision-001",
        "decision_version": 3,
        "decision_digest": None,
        "reference_contract_version": "decision-reference-v1",
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionReference(**values)


def read_reference(reference_id, version):
    return AttachmentReadReference(reference_id, version)


def decision_payload(**overrides):
    values = {
        "attachment_reference": read_reference("attachment-001", 11),
        "analysis_reference": read_reference("analysis-001", 3),
        "classification_reference": read_reference("classification-001", 7),
        "metrics_reference": read_reference("metrics-001", 19),
        "compatibility_status": AttachmentCompatibilityStatus.COMPATIBLE,
        "policy_version": "attachment-compatibility-v1",
        "evaluated_at": UTC_TIME,
    }
    values.update(overrides)
    return RealityGapAttachmentCompatibilityDecision(**values)


def envelope(**overrides):
    values = {
        "decision_reference": decision_reference(),
        "decision_payload": decision_payload(),
        "envelope_version": "decision-record-envelope-v1",
        "created_at": UTC_TIME,
    }
    values.update(overrides)
    return RealityGapCompatibilityDecisionRecordEnvelope(**values)


class CompatibilityDecisionRecordEnvelopeTests(unittest.TestCase):
    def test_valid_record_envelope_binds_typed_reference_and_payload(self):
        value = envelope()
        self.assertIsInstance(
            value.decision_reference, RealityGapCompatibilityDecisionReference
        )
        self.assertIsInstance(
            value.decision_payload, RealityGapAttachmentCompatibilityDecision
        )

    def test_version_only_decision_reference_is_preserved(self):
        value = envelope(decision_reference=decision_reference())
        self.assertEqual(value.decision_reference.decision_version, 3)
        self.assertIsNone(value.decision_reference.decision_digest)

    def test_version_and_digest_reference_are_both_preserved(self):
        value = envelope(
            decision_reference=decision_reference(
                decision_digest=DECISION_DIGEST
            )
        )
        self.assertEqual(value.decision_reference.decision_version, 3)
        self.assertEqual(
            value.decision_reference.decision_digest, DECISION_DIGEST
        )

    def test_invalid_reference_is_rejected(self):
        for value in (None, {}, "decision-001"):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionRecordEnvelopeValidationError
                ):
                    envelope(decision_reference=value)

    def test_invalid_payload_is_rejected(self):
        for value in (None, {}, "COMPATIBLE"):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionRecordEnvelopeValidationError
                ):
                    envelope(decision_payload=value)

    def test_created_at_requires_aware_time_and_normalizes_utc(self):
        with self.assertRaises(
            CompatibilityDecisionRecordEnvelopeValidationError
        ):
            envelope(created_at=datetime(2026, 7, 17, 12, 0))

        offset = timezone(timedelta(hours=3))
        value = envelope(
            created_at=datetime(2026, 7, 17, 15, 0, tzinfo=offset)
        )
        self.assertEqual(value.created_at, UTC_TIME)
        self.assertEqual(value.created_at.tzinfo, timezone.utc)

    def test_envelope_version_is_required_and_validated(self):
        for value in (None, "", "  ", "bad version"):
            with self.subTest(value=value):
                with self.assertRaises(
                    CompatibilityDecisionRecordEnvelopeValidationError
                ):
                    envelope(envelope_version=value)

    def test_envelope_and_nested_records_are_immutable(self):
        value = envelope()
        with self.assertRaises(FrozenInstanceError):
            value.envelope_version = "v2"
        with self.assertRaises(FrozenInstanceError):
            value.decision_reference.decision_version = 4
        with self.assertRaises(FrozenInstanceError):
            value.decision_payload.policy_version = "current-default"

    def test_serialization_round_trip_is_deterministic(self):
        value = envelope(
            decision_reference=decision_reference(
                decision_digest=DECISION_DIGEST
            ),
            decision_payload=decision_payload(
                compatibility_status=(
                    AttachmentCompatibilityStatus.REQUIRES_REVIEW
                )
            ),
        )
        restored = RealityGapCompatibilityDecisionRecordEnvelope.from_dict(
            value.to_dict()
        )
        self.assertEqual(restored, value)
        self.assertEqual(restored.canonical_json(), value.canonical_json())
        self.assertEqual(json.loads(value.canonical_json()), value.to_dict())

    def test_historical_identity_and_complete_payload_are_preserved(self):
        value = envelope(
            decision_reference=decision_reference(
                decision_id="historical-decision-009",
                decision_version=9,
                decision_digest=DECISION_DIGEST,
            )
        )
        restored = RealityGapCompatibilityDecisionRecordEnvelope.from_dict(
            value.to_dict()
        )
        self.assertEqual(restored.decision_reference, value.decision_reference)
        self.assertEqual(restored.decision_payload, value.decision_payload)
        self.assertEqual(
            restored.decision_payload.to_dict(), value.decision_payload.to_dict()
        )

    def test_contract_exposes_only_record_envelope_fields(self):
        self.assertEqual(
            tuple(
                item.name
                for item in fields(
                    RealityGapCompatibilityDecisionRecordEnvelope
                )
            ),
            (
                "decision_reference",
                "decision_payload",
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
        invalid_reference["decision_reference"] = {"decision_id": "partial"}
        with self.assertRaises(
            CompatibilityDecisionRecordEnvelopeValidationError
        ):
            RealityGapCompatibilityDecisionRecordEnvelope.from_dict(
                invalid_reference
            )

        invalid_payload = envelope().to_dict()
        invalid_payload["decision_payload"] = {"policy_version": "partial"}
        with self.assertRaises(
            CompatibilityDecisionRecordEnvelopeValidationError
        ):
            RealityGapCompatibilityDecisionRecordEnvelope.from_dict(
                invalid_payload
            )

        unknown = envelope().to_dict()
        unknown["resolver"] = "forbidden"
        with self.assertRaises(
            CompatibilityDecisionRecordEnvelopeValidationError
        ):
            RealityGapCompatibilityDecisionRecordEnvelope.from_dict(unknown)


if __name__ == "__main__":
    unittest.main()
