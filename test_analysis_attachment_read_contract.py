"""Focused tests for the immutable attachment read boundary."""

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
import json
import unittest

from app.intelligence.attachments import (
    AttachmentAvailabilityStatus,
    AttachmentReadReference,
    AttachmentReadValidationError,
    RealityGapAttachmentReadContract,
)


UTC_TIME = datetime(2026, 7, 16, 12, 0, tzinfo=timezone.utc)


def reference(reference_id="analysis-001", reference_version=1):
    return AttachmentReadReference(reference_id, reference_version)


def read_contract(**overrides):
    values = {
        "attachment_id": "attachment-001",
        "analysis_reference": reference("analysis-001", 3),
        "classification_reference": reference("classification-001", 5),
        "metrics_reference": reference("metrics-001", 2),
        "attachment_version": 7,
        "availability_status": AttachmentAvailabilityStatus.AVAILABLE,
        "created_at": UTC_TIME,
    }
    values.update(overrides)
    return RealityGapAttachmentReadContract(**values)


class AttachmentReadReferenceTests(unittest.TestCase):
    def test_reference_is_immutable_and_versioned(self):
        value = reference(reference_version=9)
        self.assertEqual(value.reference_version, 9)
        with self.assertRaises(FrozenInstanceError):
            value.reference_version = 10

    def test_reference_requires_identity_and_positive_version(self):
        for identity, version in (("", 1), ("id", 0), ("id", True)):
            with self.subTest(identity=identity, version=version):
                with self.assertRaises(AttachmentReadValidationError):
                    reference(identity, version)

    def test_reference_round_trip_is_exact(self):
        value = reference("classification-001", 4)
        self.assertEqual(AttachmentReadReference.from_dict(value.to_dict()), value)


class RealityGapAttachmentReadContractTests(unittest.TestCase):
    def test_valid_contract_is_immutable(self):
        value = read_contract()
        with self.assertRaises(FrozenInstanceError):
            value.attachment_id = "other"

    def test_exposes_only_approved_fields(self):
        self.assertEqual(
            tuple(item.name for item in fields(RealityGapAttachmentReadContract)),
            (
                "attachment_id",
                "analysis_reference",
                "classification_reference",
                "metrics_reference",
                "attachment_version",
                "availability_status",
                "created_at",
            ),
        )
        forbidden = {
            "evidence",
            "candidates",
            "projection",
            "mapping",
            "classification_payload",
            "metrics_payload",
        }
        self.assertTrue(forbidden.isdisjoint(read_contract().to_dict()))

    def test_versions_are_validated_independently(self):
        value = read_contract(
            attachment_version=11,
            analysis_reference=reference("analysis-001", 2),
            classification_reference=reference("classification-001", 7),
            metrics_reference=reference("metrics-001", 19),
        )
        self.assertEqual(
            (
                value.attachment_version,
                value.analysis_reference.reference_version,
                value.classification_reference.reference_version,
                value.metrics_reference.reference_version,
            ),
            (11, 2, 7, 19),
        )
        with self.assertRaises(AttachmentReadValidationError):
            read_contract(attachment_version=False)

    def test_required_reference_types_are_enforced(self):
        for field_name in (
            "analysis_reference",
            "classification_reference",
            "metrics_reference",
        ):
            with self.subTest(field_name=field_name):
                with self.assertRaises(AttachmentReadValidationError):
                    read_contract(**{field_name: None})

    def test_identities_must_remain_distinct(self):
        with self.assertRaises(AttachmentReadValidationError):
            read_contract(metrics_reference=reference("analysis-001", 8))

    def test_allowed_availability_statuses(self):
        for status in AttachmentAvailabilityStatus:
            with self.subTest(status=status):
                value = read_contract(availability_status=status.value)
                self.assertIs(value.availability_status, status)
        with self.assertRaises(AttachmentReadValidationError):
            read_contract(availability_status="STALE")

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(AttachmentReadValidationError):
            read_contract(created_at=datetime(2026, 7, 16, 12, 0))

    def test_timestamp_is_normalized_to_utc(self):
        offset = timezone(timedelta(hours=3))
        value = read_contract(
            created_at=datetime(2026, 7, 16, 15, 0, tzinfo=offset)
        )
        self.assertEqual(value.created_at, UTC_TIME)
        self.assertEqual(value.created_at.tzinfo, timezone.utc)

    def test_to_dict_and_from_dict_round_trip(self):
        value = read_contract()
        restored = RealityGapAttachmentReadContract.from_dict(value.to_dict())
        self.assertEqual(restored, value)
        self.assertIsInstance(
            restored.availability_status, AttachmentAvailabilityStatus
        )
        self.assertEqual(restored.created_at.tzinfo, timezone.utc)

    def test_canonical_json_is_deterministic(self):
        value = read_contract()
        first = value.canonical_json()
        second = RealityGapAttachmentReadContract.from_dict(
            json.loads(first)
        ).canonical_json()
        self.assertEqual(first, second)
        self.assertEqual(json.loads(first), value.to_dict())

    def test_unknown_or_missing_serialized_fields_are_rejected(self):
        valid = read_contract().to_dict()
        for payload in (
            dict(valid, raw_evidence=[]),
            {key: item for key, item in valid.items() if key != "metrics_reference"},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(AttachmentReadValidationError):
                    RealityGapAttachmentReadContract.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
