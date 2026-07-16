"""Focused tests for immutable attachment compatibility contracts."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import json
import unittest

from app.intelligence.attachments import (
    AttachmentCompatibilityStatus,
    AttachmentCompatibilityValidationError,
    AttachmentReadReference,
    AttachmentRevisionAxis,
    AttachmentVersionCompatibilityRule,
    AttachmentVersionCondition,
    RealityGapAttachmentCompatibilityDecision,
    RealityGapAttachmentCompatibilityPolicy,
    canonical_version_rules,
)


UTC_TIME = datetime(2026, 7, 16, 15, 0, tzinfo=timezone.utc)


def reference(reference_id, version):
    return AttachmentReadReference(reference_id, version)


def policy(**overrides):
    values = {"policy_version": "attachment-compatibility-v1"}
    values.update(overrides)
    return RealityGapAttachmentCompatibilityPolicy(**values)


def decision(**overrides):
    values = {
        "attachment_reference": reference("attachment-001", 11),
        "analysis_reference": reference("analysis-001", 3),
        "classification_reference": reference("classification-001", 7),
        "metrics_reference": reference("metrics-001", 19),
        "compatibility_status": AttachmentCompatibilityStatus.COMPATIBLE,
        "policy_version": "attachment-compatibility-v1",
        "evaluated_at": UTC_TIME,
    }
    values.update(overrides)
    return RealityGapAttachmentCompatibilityDecision(**values)


class CompatibilityPolicyTests(unittest.TestCase):
    def test_canonical_compatible_rules(self):
        outcomes = {
            item.condition: item.compatibility_status
            for item in canonical_version_rules()
        }
        self.assertIs(
            outcomes[AttachmentVersionCondition.SAME_CONTRACT_VERSION],
            AttachmentCompatibilityStatus.COMPATIBLE,
        )
        self.assertIs(
            outcomes[AttachmentVersionCondition.PATCH_VERSION_CHANGE],
            AttachmentCompatibilityStatus.COMPATIBLE,
        )

    def test_major_version_mismatch_is_incompatible(self):
        outcomes = {
            item.condition: item.compatibility_status
            for item in canonical_version_rules()
        }
        self.assertIs(
            outcomes[AttachmentVersionCondition.MAJOR_VERSION_MISMATCH],
            AttachmentCompatibilityStatus.INCOMPATIBLE,
        )

    def test_minor_and_unknown_versions_require_review(self):
        outcomes = {
            item.condition: item.compatibility_status
            for item in canonical_version_rules()
        }
        for condition in (
            AttachmentVersionCondition.MINOR_VERSION_EVOLUTION,
            AttachmentVersionCondition.UNKNOWN_VERSION,
        ):
            with self.subTest(condition=condition):
                self.assertIs(
                    outcomes[condition],
                    AttachmentCompatibilityStatus.REQUIRES_REVIEW,
                )

    def test_rule_rejects_noncanonical_outcome(self):
        with self.assertRaises(AttachmentCompatibilityValidationError):
            AttachmentVersionCompatibilityRule(
                AttachmentVersionCondition.MAJOR_VERSION_MISMATCH,
                AttachmentCompatibilityStatus.COMPATIBLE,
            )

    def test_policy_is_immutable_and_rules_are_complete(self):
        value = policy()
        with self.assertRaises(FrozenInstanceError):
            value.policy_version = "later"
        with self.assertRaises(TypeError):
            value.version_rules[0] = value.version_rules[1]
        with self.assertRaises(AttachmentCompatibilityValidationError):
            policy(version_rules=canonical_version_rules()[:-1])

    def test_independent_version_axes_are_required(self):
        value = policy()
        self.assertEqual(
            value.independent_version_axes,
            (
                AttachmentRevisionAxis.ATTACHMENT,
                AttachmentRevisionAxis.ANALYSIS,
                AttachmentRevisionAxis.CLASSIFICATION,
                AttachmentRevisionAxis.METRICS,
            ),
        )
        with self.assertRaises(AttachmentCompatibilityValidationError):
            policy(independent_version_axes=value.independent_version_axes[:-1])

    def test_historical_integrity_cannot_be_disabled(self):
        for override in (
            {"historical_integrity_required": False},
            {"preserve_historical_references": False},
            {"allow_current_default_substitution": True},
        ):
            with self.subTest(override=override):
                with self.assertRaises(AttachmentCompatibilityValidationError):
                    policy(**override)

    def test_policy_round_trip_and_deterministic_json(self):
        value = policy()
        restored = RealityGapAttachmentCompatibilityPolicy.from_dict(
            value.to_dict()
        )
        self.assertEqual(restored, value)
        self.assertEqual(restored.canonical_json(), value.canonical_json())
        self.assertEqual(json.loads(value.canonical_json()), value.to_dict())


class CompatibilityDecisionTests(unittest.TestCase):
    def test_decision_preserves_four_independent_references(self):
        value = decision()
        self.assertEqual(
            (
                value.attachment_reference.reference_version,
                value.analysis_reference.reference_version,
                value.classification_reference.reference_version,
                value.metrics_reference.reference_version,
            ),
            (11, 3, 7, 19),
        )

    def test_all_decision_categories_are_supported(self):
        for status in AttachmentCompatibilityStatus:
            with self.subTest(status=status):
                self.assertIs(
                    decision(compatibility_status=status.value).compatibility_status,
                    status,
                )

    def test_decision_is_immutable_and_references_remain_historical(self):
        value = decision()
        with self.assertRaises(FrozenInstanceError):
            value.analysis_reference = reference("current-analysis", 99)
        self.assertEqual(value.analysis_reference, reference("analysis-001", 3))

    def test_reference_identity_and_type_validation(self):
        with self.assertRaises(AttachmentCompatibilityValidationError):
            decision(metrics_reference=reference("analysis-001", 8))
        with self.assertRaises(AttachmentCompatibilityValidationError):
            decision(classification_reference=None)

    def test_evaluated_at_requires_aware_time_and_normalizes_utc(self):
        with self.assertRaises(AttachmentCompatibilityValidationError):
            decision(evaluated_at=datetime(2026, 7, 16, 15, 0))
        offset = timezone(timedelta(hours=3))
        value = decision(
            evaluated_at=datetime(2026, 7, 16, 18, 0, tzinfo=offset)
        )
        self.assertEqual(value.evaluated_at, UTC_TIME)
        self.assertEqual(value.evaluated_at.tzinfo, timezone.utc)

    def test_decision_round_trip_and_canonical_json(self):
        value = decision(
            compatibility_status=AttachmentCompatibilityStatus.REQUIRES_REVIEW
        )
        restored = RealityGapAttachmentCompatibilityDecision.from_dict(
            value.to_dict()
        )
        self.assertEqual(restored, value)
        self.assertEqual(restored.canonical_json(), value.canonical_json())

    def test_unknown_serialized_payload_is_rejected(self):
        payload = decision().to_dict()
        payload["current_default"] = "forbidden"
        with self.assertRaises(AttachmentCompatibilityValidationError):
            RealityGapAttachmentCompatibilityDecision.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
