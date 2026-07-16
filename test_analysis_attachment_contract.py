"""Focused tests for the immutable RealityGapAnalysisAttachment contract."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import json
import unittest

from app.intelligence.attachments import (
    AnalysisReference,
    AttachmentFailureCategory,
    AttachmentValidationError,
    ClassificationReference,
    MetricSetReference,
    RealityGapAnalysisAttachment,
)


UTC_TIME = datetime(2026, 7, 16, 10, 0, tzinfo=timezone.utc)
CLASSIFICATION_DIGEST = "sha256:" + ("a" * 64)
METRIC_DIGEST = "sha256:" + ("b" * 64)


def analysis_reference(**overrides):
    values = {"analysis_id": "gap-001", "analysis_version": 3}
    values.update(overrides)
    return AnalysisReference(**values)


def classification_reference(**overrides):
    values = {
        "classification_id": "classification-001",
        "canonical_snapshot_digest": CLASSIFICATION_DIGEST,
    }
    values.update(overrides)
    return ClassificationReference(**values)


def metric_reference(**overrides):
    values = {
        "metric_set_id": "metric-set-001",
        "canonical_snapshot_digest": METRIC_DIGEST,
    }
    values.update(overrides)
    return MetricSetReference(**values)


def attachment(**overrides):
    values = {
        "attachment_id": "attachment-001",
        "attachment_version": 1,
        "analysis_reference": analysis_reference(),
        "classification_reference": classification_reference(),
        "metric_set_reference": metric_reference(),
        "attachment_policy_version": "attachment-v1",
        "created_at": UTC_TIME,
        "metadata": {
            "trace_reference": "attachment-trace-001",
            "lineage": {"source": ["classification", "metrics"]},
        },
    }
    values.update(overrides)
    return RealityGapAnalysisAttachment(**values)


class AnalysisAttachmentContractTests(unittest.TestCase):
    def test_immutable_construction_and_defensive_metadata_conversion(self):
        source = {"nested": {"items": ["a", "b"]}}
        value = attachment(metadata=source)
        source["nested"]["items"].append("later")

        self.assertEqual(value.metadata["nested"]["items"], ("a", "b"))
        with self.assertRaises(FrozenInstanceError):
            value.attachment_version = 2
        with self.assertRaises(TypeError):
            value.metadata["new"] = "mutation"

    def test_deterministic_serialization_and_equal_byte_stability(self):
        first = attachment(metadata={"z": 1, "a": {"y": 2, "x": 3}})
        second = attachment(metadata={"a": {"x": 3, "y": 2}, "z": 1})

        self.assertEqual(first, second)
        self.assertEqual(first.to_json_bytes(), second.to_json_bytes())
        self.assertEqual(
            json.loads(first.to_json_bytes().decode("utf-8")),
            first.to_dict(),
        )

    def test_round_trip_reconstruction_preserves_nested_reference_types(self):
        value = attachment()
        restored = RealityGapAnalysisAttachment.from_dict(value.to_dict())

        self.assertEqual(restored, value)
        self.assertIsInstance(restored.analysis_reference, AnalysisReference)
        self.assertIsInstance(
            restored.classification_reference, ClassificationReference
        )
        self.assertIsInstance(restored.metric_set_reference, MetricSetReference)
        self.assertEqual(restored.created_at.tzinfo, timezone.utc)

    def test_analysis_identity_is_preserved(self):
        value = attachment(
            analysis_reference=analysis_reference(
                analysis_id="gap-special", analysis_version=7
            )
        )
        self.assertEqual(value.analysis_reference.analysis_id, "gap-special")
        self.assertEqual(value.analysis_reference.analysis_version, 7)
        self.assertEqual(
            value.to_dict()["analysis_reference"],
            {"analysis_id": "gap-special", "analysis_version": 7},
        )

    def test_classification_reference_is_preserved(self):
        value = attachment()
        self.assertEqual(
            value.classification_reference.classification_id,
            "classification-001",
        )
        self.assertEqual(
            value.classification_reference.canonical_snapshot_digest,
            CLASSIFICATION_DIGEST,
        )

    def test_metric_reference_is_preserved(self):
        value = attachment()
        self.assertEqual(value.metric_set_reference.metric_set_id, "metric-set-001")
        self.assertEqual(
            value.metric_set_reference.canonical_snapshot_digest,
            METRIC_DIGEST,
        )

    def test_all_primary_identities_remain_separate(self):
        value = attachment()
        identities = {
            value.attachment_id,
            value.analysis_reference.analysis_id,
            value.classification_reference.classification_id,
            value.metric_set_reference.metric_set_id,
            value.metadata["trace_reference"],
        }
        self.assertEqual(len(identities), 5)

        with self.assertRaises(AttachmentValidationError) as caught:
            attachment(attachment_id="gap-001")
        self.assertEqual(
            caught.exception.category,
            AttachmentFailureCategory.ANALYSIS_MISMATCH,
        )

    def test_versions_are_independent(self):
        value = attachment(
            attachment_version=9,
            analysis_reference=analysis_reference(analysis_version=2),
            attachment_policy_version="attachment-v4",
        )
        self.assertEqual(value.attachment_version, 9)
        self.assertEqual(value.analysis_reference.analysis_version, 2)
        self.assertEqual(value.attachment_policy_version, "attachment-v4")

    def test_attachment_and_analysis_version_validation(self):
        cases = (
            ({"attachment_version": 0}, AttachmentFailureCategory.VERSION_CONFLICT),
            ({"attachment_version": True}, AttachmentFailureCategory.VERSION_CONFLICT),
        )
        for overrides, expected in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(AttachmentValidationError) as caught:
                    attachment(**overrides)
                self.assertEqual(caught.exception.category, expected)

        with self.assertRaises(AttachmentValidationError) as caught:
            analysis_reference(analysis_version=0)
        self.assertEqual(
            caught.exception.category,
            AttachmentFailureCategory.VERSION_CONFLICT,
        )

    def test_missing_classification_failure_has_no_partial_attachment(self):
        with self.assertRaises(AttachmentValidationError) as caught:
            attachment(classification_reference=None)
        self.assertEqual(
            caught.exception.category,
            AttachmentFailureCategory.MISSING_CLASSIFICATION,
        )

        payload = attachment().to_dict()
        payload.pop("classification_reference")
        with self.assertRaises(AttachmentValidationError) as caught:
            RealityGapAnalysisAttachment.from_dict(payload)
        self.assertEqual(
            caught.exception.category,
            AttachmentFailureCategory.MISSING_CLASSIFICATION,
        )

    def test_missing_metrics_failure_has_no_partial_attachment(self):
        with self.assertRaises(AttachmentValidationError) as caught:
            attachment(metric_set_reference=None)
        self.assertEqual(
            caught.exception.category,
            AttachmentFailureCategory.MISSING_METRICS,
        )

        payload = attachment().to_dict()
        payload["metric_set_reference"] = None
        with self.assertRaises(AttachmentValidationError) as caught:
            RealityGapAnalysisAttachment.from_dict(payload)
        self.assertEqual(
            caught.exception.category,
            AttachmentFailureCategory.MISSING_METRICS,
        )

    def test_invalid_reference_digest_is_rejected(self):
        invalid = (
            "",
            "a" * 64,
            "sha256:ABCDEF" + ("0" * 58),
            "sha256:" + ("g" * 64),
            "sha256:" + ("a" * 63),
        )
        for digest in invalid:
            with self.subTest(digest=digest):
                with self.assertRaises(AttachmentValidationError) as caught:
                    classification_reference(canonical_snapshot_digest=digest)
                self.assertEqual(
                    caught.exception.category,
                    AttachmentFailureCategory.INVALID_REFERENCE,
                )

    def test_policy_conflict_is_categorized(self):
        for overrides in (
            {"attachment_policy_version": "bad policy"},
            {
                "metadata": {
                    "attachment_policy_version": "attachment-v2",
                }
            },
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(AttachmentValidationError) as caught:
                    attachment(**overrides)
                self.assertEqual(
                    caught.exception.category,
                    AttachmentFailureCategory.POLICY_CONFLICT,
                )

    def test_analysis_metadata_mismatch_is_categorized(self):
        with self.assertRaises(AttachmentValidationError) as caught:
            attachment(metadata={"analysis_version": 99})
        self.assertEqual(
            caught.exception.category,
            AttachmentFailureCategory.ANALYSIS_MISMATCH,
        )

    def test_timestamp_requires_awareness_and_normalizes_to_utc(self):
        with self.assertRaises(AttachmentValidationError) as caught:
            attachment(created_at=datetime(2026, 7, 16, 10, 0))
        self.assertEqual(
            caught.exception.category,
            AttachmentFailureCategory.INVALID_REFERENCE,
        )

        offset = timezone(timedelta(hours=2))
        value = attachment(
            created_at=datetime(2026, 7, 16, 12, 0, tzinfo=offset)
        )
        self.assertEqual(value.created_at, UTC_TIME)
        self.assertEqual(value.created_at.tzinfo, timezone.utc)

    def test_unsupported_metadata_payload_is_rejected(self):
        with self.assertRaises(AttachmentValidationError) as caught:
            attachment(metadata={"unordered": {"a", "b"}})
        self.assertEqual(
            caught.exception.category,
            AttachmentFailureCategory.INVALID_REFERENCE,
        )

    def test_serialized_unknown_fields_are_rejected(self):
        payload = attachment().to_dict()
        payload["future_output"] = "forbidden"
        with self.assertRaises(AttachmentValidationError) as caught:
            RealityGapAnalysisAttachment.from_dict(payload)
        self.assertEqual(
            caught.exception.category,
            AttachmentFailureCategory.INVALID_REFERENCE,
        )


if __name__ == "__main__":
    unittest.main()
