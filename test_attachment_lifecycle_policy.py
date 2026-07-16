"""Focused tests for the immutable attachment lifecycle policy."""

from dataclasses import FrozenInstanceError
import json
import unittest

from app.intelligence.attachments import (
    AttachmentLifecycleState,
    AttachmentLifecycleTransition,
    AttachmentLifecycleValidationError,
    AttachmentRevisionAxis,
    RealityGapAttachmentLifecyclePolicy,
    canonical_lifecycle_transitions,
)


def policy(**overrides):
    values = {
        "lifecycle_state": AttachmentLifecycleState.CREATED,
        "policy_version": "attachment-lifecycle-v1",
        "revision_policy_identifier": "independent-revisions-v1",
    }
    values.update(overrides)
    return RealityGapAttachmentLifecyclePolicy(**values)


class AttachmentLifecycleTransitionTests(unittest.TestCase):
    def test_valid_forward_transitions(self):
        expected = (
            (AttachmentLifecycleState.CREATED, AttachmentLifecycleState.ACTIVE),
            (AttachmentLifecycleState.ACTIVE, AttachmentLifecycleState.SUPERSEDED),
            (AttachmentLifecycleState.SUPERSEDED, AttachmentLifecycleState.ARCHIVED),
        )
        self.assertEqual(
            tuple(
                (transition.from_state, transition.to_state)
                for transition in canonical_lifecycle_transitions()
            ),
            expected,
        )

    def test_invalid_backward_skip_and_same_state_transitions(self):
        invalid = (
            (AttachmentLifecycleState.ACTIVE, AttachmentLifecycleState.CREATED),
            (AttachmentLifecycleState.CREATED, AttachmentLifecycleState.SUPERSEDED),
            (AttachmentLifecycleState.ACTIVE, AttachmentLifecycleState.ARCHIVED),
            (AttachmentLifecycleState.ARCHIVED, AttachmentLifecycleState.ACTIVE),
            (AttachmentLifecycleState.ACTIVE, AttachmentLifecycleState.ACTIVE),
        )
        for from_state, to_state in invalid:
            with self.subTest(from_state=from_state, to_state=to_state):
                with self.assertRaises(AttachmentLifecycleValidationError):
                    AttachmentLifecycleTransition(from_state, to_state)

    def test_transition_round_trip(self):
        value = AttachmentLifecycleTransition("ACTIVE", "SUPERSEDED")
        self.assertEqual(
            AttachmentLifecycleTransition.from_dict(value.to_dict()), value
        )


class RealityGapAttachmentLifecyclePolicyTests(unittest.TestCase):
    def test_policy_is_immutable(self):
        value = policy()
        with self.assertRaises(FrozenInstanceError):
            value.policy_version = "later"
        with self.assertRaises(TypeError):
            value.allowed_transitions[0] = value.allowed_transitions[1]

    def test_all_lifecycle_states_are_supported(self):
        for state in AttachmentLifecycleState:
            with self.subTest(state=state):
                self.assertIs(policy(lifecycle_state=state.value).lifecycle_state, state)
        with self.assertRaises(AttachmentLifecycleValidationError):
            policy(lifecycle_state="DELETED")

    def test_policy_requires_canonical_transition_graph(self):
        with self.assertRaises(AttachmentLifecycleValidationError):
            policy(allowed_transitions=canonical_lifecycle_transitions()[:-1])
        with self.assertRaises(AttachmentLifecycleValidationError):
            policy(allowed_transitions=reversed(canonical_lifecycle_transitions()))

    def test_revision_axes_are_independent_and_complete(self):
        value = policy()
        self.assertEqual(
            value.independent_revision_axes,
            (
                AttachmentRevisionAxis.ATTACHMENT,
                AttachmentRevisionAxis.ANALYSIS,
                AttachmentRevisionAxis.CLASSIFICATION,
                AttachmentRevisionAxis.METRICS,
            ),
        )
        with self.assertRaises(AttachmentLifecycleValidationError):
            policy(
                independent_revision_axes=(
                    AttachmentRevisionAxis.ATTACHMENT,
                    AttachmentRevisionAxis.ANALYSIS,
                )
            )

    def test_historical_preservation_invariants_cannot_be_disabled(self):
        invalid = (
            {"immutable_historical_attachments": False},
            {"preserve_historical_references": False},
            {"allow_current_default_substitution": True},
        )
        for override in invalid:
            with self.subTest(override=override):
                with self.assertRaises(AttachmentLifecycleValidationError):
                    policy(**override)

    def test_required_policy_and_revision_identifiers(self):
        for override in (
            {"policy_version": ""},
            {"revision_policy_identifier": "  "},
        ):
            with self.subTest(override=override):
                with self.assertRaises(AttachmentLifecycleValidationError):
                    policy(**override)

    def test_serialization_round_trip(self):
        value = policy(lifecycle_state=AttachmentLifecycleState.SUPERSEDED)
        restored = RealityGapAttachmentLifecyclePolicy.from_dict(value.to_dict())
        self.assertEqual(restored, value)
        self.assertIsInstance(restored.lifecycle_state, AttachmentLifecycleState)
        self.assertIsInstance(
            restored.independent_revision_axes[0], AttachmentRevisionAxis
        )

    def test_canonical_json_is_deterministic(self):
        value = policy()
        first = value.canonical_json()
        restored = RealityGapAttachmentLifecyclePolicy.from_dict(json.loads(first))
        self.assertEqual(restored.canonical_json(), first)
        self.assertEqual(json.loads(first), value.to_dict())

    def test_unknown_serialized_fields_are_rejected(self):
        payload = policy().to_dict()
        payload["runtime_service"] = "forbidden"
        with self.assertRaises(AttachmentLifecycleValidationError):
            RealityGapAttachmentLifecyclePolicy.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
