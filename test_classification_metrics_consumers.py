"""Focused tests for pure read-only Classification and Metrics consumers."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import unittest

from app.intelligence.classification_metrics import (
    ClassificationAssignment,
    ClassificationConsumerError,
    ClassificationConsumerFailureCategory,
    ClassificationConsumerPolicy,
    MetricAvailability,
    MetricIndicator,
    MetricsConsumerError,
    MetricsConsumerFailureCategory,
    MetricsConsumerPolicy,
    RealityGapConsumerContext,
    classify_reality_gap,
    measure_reality_gap,
)
from app.intelligence.reality_gap.enums import (
    RealityGapDimension,
    RealityGapEvidenceEligibility,
    RealityGapEvidenceRelation,
    RealityGapEvidenceType,
    RootCauseCategory,
    RootCauseDisposition,
    RootCauseRole,
)
from app.intelligence.reality_gap.models import (
    RealityGapEvidenceReference,
    RootCauseCandidate,
)


EVALUATED_AT = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)
WINDOW_START = EVALUATED_AT - timedelta(hours=1)


def candidate(**overrides):
    values = {
        "candidate_id": "projection-001",
        "category": RootCauseCategory.OBSERVABILITY_LIMITATION,
        "subject": "Funding context",
        "description": "Historical funding evidence was incomplete.",
        "role": RootCauseRole.CONTRIBUTING_CANDIDATE,
        "disposition": RootCauseDisposition.PARTIALLY_SUPPORTED,
        "confidence": None,
        "temporal_precedence": None,
        "direct_relevance": None,
        "evidence_coverage": None,
        "independent_support_count": 1,
        "supporting_evidence_refs": ("evidence-001",),
        "contradicting_evidence_refs": ("evidence-002",),
        "parent_candidate_id": None,
        "child_candidate_ids": (),
        "limitations": ("one provider unavailable",),
        "alternative_candidate_ids": (),
        "rejection_reason": None,
        "policy_version": "mapping-v1",
        "metadata": {"source_projection_id": "projection-001"},
    }
    values.update(overrides)
    return RootCauseCandidate(**values)


def evidence(evidence_id, availability="AVAILABLE", **overrides):
    values = {
        "evidence_id": evidence_id,
        "evidence_type": RealityGapEvidenceType.OBSERVABILITY_FACT,
        "relation": RealityGapEvidenceRelation.SUPPORTS,
        "eligibility": RealityGapEvidenceEligibility.ELIGIBLE,
        "artifact_id": "artifact-{0}".format(evidence_id),
        "timeline_id": "timeline-001",
        "timeline_version": 3,
        "entry_id": "entry-{0}".format(evidence_id),
        "observed_at": WINDOW_START + timedelta(minutes=30),
        "factor_name": "funding",
        "measured_value": 65.0 if availability == "AVAILABLE" else None,
        "availability": availability,
        "delta_state": None,
        "prior_value": None,
        "new_value": None,
        "criterion_reference": "criterion-funding",
        "rejection_reason": None,
        "quality": 80.0,
        "metadata": {},
    }
    values.update(overrides)
    return RealityGapEvidenceReference(**values)


def context(**overrides):
    values = {
        "analysis_reference": "analysis-001:v3",
        "analysis_version": 3,
        "analysis_policy_version": "analysis-v1",
        "evaluated_at": EVALUATED_AT,
        "eligible_window_start": WINDOW_START,
        "eligible_window_end": EVALUATED_AT,
        "candidate_references": ("projection-001",),
        "evidence_references": ("evidence-002", "evidence-001"),
        "metadata": {"timeline": {"version": 3}},
    }
    values.update(overrides)
    return RealityGapConsumerContext(**values)


def classification_policy(**overrides):
    values = {
        "policy_version": "classification-v1",
        "expected_analysis_policy_version": "analysis-v1",
        "expected_candidate_policy_version": "mapping-v1",
        "assignments": {
            RootCauseCategory.OBSERVABILITY_LIMITATION: ClassificationAssignment(
                dimensions=(RealityGapDimension.OBSERVABILITY,),
                categories=("OBSERVABILITY_GAP",),
            )
        },
        "metadata": {},
    }
    values.update(overrides)
    return ClassificationConsumerPolicy(**values)


def metrics_policy(**overrides):
    values = {
        "policy_version": "metrics-v1",
        "expected_analysis_policy_version": "analysis-v1",
        "expected_candidate_policy_version": "mapping-v1",
        "indicators": (
            MetricIndicator.REFERENCE_COVERAGE,
            MetricIndicator.EVIDENCE_AVAILABILITY_RATIO,
        ),
        "metadata": {},
    }
    values.update(overrides)
    return MetricsConsumerPolicy(**values)


INPUT_REFS = ("projection-001", "evidence-001", "evidence-002")


class ClassificationConsumerTests(unittest.TestCase):
    def test_valid_classification_is_deterministic(self):
        first = classify_reality_gap(
            candidate(), context(), classification_policy(), reversed(INPUT_REFS)
        )
        second = classify_reality_gap(
            candidate(), context(), classification_policy(), INPUT_REFS
        )

        self.assertEqual(first, second)
        self.assertEqual(first.to_json_bytes(), second.to_json_bytes())
        self.assertEqual(first.dimensions, (RealityGapDimension.OBSERVABILITY,))
        self.assertEqual(first.categories, ("OBSERVABILITY_GAP",))

    def test_output_is_immutable_and_input_is_not_mutated(self):
        source_assignments = {
            RootCauseCategory.OBSERVABILITY_LIMITATION: ClassificationAssignment(
                (RealityGapDimension.OBSERVABILITY,), ("OBSERVABILITY_GAP",)
            )
        }
        policy = classification_policy(assignments=source_assignments)
        source_assignments.clear()
        source_candidate = candidate()
        before = source_candidate.to_dict()

        output = classify_reality_gap(
            source_candidate, context(), policy, INPUT_REFS
        )

        self.assertEqual(source_candidate.to_dict(), before)
        self.assertIn(RootCauseCategory.OBSERVABILITY_LIMITATION, policy.assignments)
        with self.assertRaises(FrozenInstanceError):
            output.classification_id = "changed"

    def test_dimension_validation_rejects_unknown(self):
        with self.assertRaises(ClassificationConsumerError) as caught:
            ClassificationAssignment(
                dimensions=(RealityGapDimension.UNKNOWN,),
                categories=("OBSERVABILITY_GAP",),
            )
        self.assertEqual(
            caught.exception.category,
            ClassificationConsumerFailureCategory.UNSUPPORTED_DIMENSION,
        )

    def test_category_validation_rejects_noncanonical_policy_value(self):
        with self.assertRaises(ClassificationConsumerError) as caught:
            ClassificationAssignment(
                dimensions=(RealityGapDimension.OBSERVABILITY,),
                categories=("not canonical",),
            )
        self.assertEqual(
            caught.exception.category,
            ClassificationConsumerFailureCategory.POLICY_MISMATCH,
        )

    def test_policy_version_mismatch_is_rejected(self):
        policy = classification_policy(expected_candidate_policy_version="mapping-v2")
        with self.assertRaises(ClassificationConsumerError) as caught:
            classify_reality_gap(candidate(), context(), policy, INPUT_REFS)
        self.assertEqual(
            caught.exception.category,
            ClassificationConsumerFailureCategory.VERSION_CONFLICT,
        )

    def test_unapproved_reference_is_anti_hindsight_rejected(self):
        with self.assertRaises(ClassificationConsumerError) as caught:
            classify_reality_gap(
                candidate(),
                context(),
                classification_policy(),
                INPUT_REFS + ("future-evidence",),
            )
        self.assertEqual(
            caught.exception.category,
            ClassificationConsumerFailureCategory.INVALID_INPUT_REFERENCE,
        )

    def test_missing_assignment_returns_no_partial_classification(self):
        policy = classification_policy(
            assignments={
                RootCauseCategory.FACTOR_WEAKENING: ClassificationAssignment(
                    (RealityGapDimension.MARKET,), ("MARKET_GAP",)
                )
            }
        )
        with self.assertRaises(ClassificationConsumerError) as caught:
            classify_reality_gap(candidate(), context(), policy, INPUT_REFS)
        self.assertEqual(
            caught.exception.category,
            ClassificationConsumerFailureCategory.UNSUPPORTED_DIMENSION,
        )


class MetricsConsumerTests(unittest.TestCase):
    def test_valid_metrics_are_deterministic(self):
        source = (evidence("evidence-002"), evidence("evidence-001"))
        first = measure_reality_gap(
            candidate(), source, context(), metrics_policy(), reversed(INPUT_REFS)
        )
        second = measure_reality_gap(
            candidate(), reversed(source), context(), metrics_policy(), INPUT_REFS
        )

        self.assertEqual(first, second)
        self.assertEqual(first.to_json_bytes(), second.to_json_bytes())
        self.assertEqual(first.metrics["reference_coverage"].value, 100.0)
        self.assertEqual(
            first.metrics["evidence_availability_ratio"].value, 100.0
        )

    def test_output_and_policy_are_immutable(self):
        policy = metrics_policy()
        output = measure_reality_gap(
            candidate(),
            (evidence("evidence-001"), evidence("evidence-002")),
            context(),
            policy,
            INPUT_REFS,
        )
        with self.assertRaises(FrozenInstanceError):
            policy.policy_version = "changed"
        with self.assertRaises(TypeError):
            output.metrics["new"] = output.metrics["reference_coverage"]

    def test_availability_is_preserved_with_partial_available_evidence(self):
        output = measure_reality_gap(
            candidate(),
            (evidence("evidence-001"), evidence("evidence-002", "MISSING")),
            context(),
            metrics_policy(),
            INPUT_REFS,
        )
        metric = output.metrics["evidence_availability_ratio"]
        self.assertEqual(metric.availability, MetricAvailability.AVAILABLE)
        self.assertEqual(metric.value, 50.0)

    def test_missing_is_not_zero(self):
        output = measure_reality_gap(
            candidate(),
            (
                evidence("evidence-001", "MISSING"),
                evidence("evidence-002", "MISSING"),
            ),
            context(),
            metrics_policy(),
            INPUT_REFS,
        )
        metric = output.metrics["evidence_availability_ratio"]
        self.assertEqual(metric.availability, MetricAvailability.MISSING)
        self.assertIsNone(metric.value)

    def test_unsupported_is_not_zero(self):
        output = measure_reality_gap(
            candidate(),
            (
                evidence("evidence-001", "UNSUPPORTED"),
                evidence("evidence-002", "UNSUPPORTED"),
            ),
            context(),
            metrics_policy(),
            INPUT_REFS,
        )
        metric = output.metrics["evidence_availability_ratio"]
        self.assertEqual(metric.availability, MetricAvailability.UNSUPPORTED)
        self.assertIsNone(metric.value)

    def test_metric_policy_rejects_unknown_indicator(self):
        with self.assertRaises(MetricsConsumerError) as caught:
            metrics_policy(indicators=("truth_score",))
        self.assertEqual(
            caught.exception.category,
            MetricsConsumerFailureCategory.UNSUPPORTED_METRIC,
        )

    def test_future_evidence_is_anti_hindsight_rejected(self):
        future = evidence(
            "evidence-001",
            observed_at=EVALUATED_AT + timedelta(seconds=1),
        )
        with self.assertRaises(MetricsConsumerError) as caught:
            measure_reality_gap(
                candidate(),
                (future, evidence("evidence-002")),
                context(),
                metrics_policy(),
                INPUT_REFS,
            )
        self.assertEqual(
            caught.exception.category,
            MetricsConsumerFailureCategory.INVALID_INPUT_REFERENCE,
        )

    def test_no_resolved_evidence_preserves_missing_and_measured_coverage(self):
        output = measure_reality_gap(
            candidate(), (), context(), metrics_policy(), INPUT_REFS
        )
        self.assertEqual(
            output.metrics["evidence_availability_ratio"].availability,
            MetricAvailability.MISSING,
        )
        self.assertIsNone(output.metrics["evidence_availability_ratio"].value)
        self.assertEqual(output.metrics["reference_coverage"].value, 0.0)
        self.assertEqual(
            output.metrics["reference_coverage"].availability,
            MetricAvailability.AVAILABLE,
        )


class ConsumerIntegrationTests(unittest.TestCase):
    def test_lineage_and_identity_remain_separate(self):
        classification = classify_reality_gap(
            candidate(), context(), classification_policy(), INPUT_REFS
        )
        metrics = measure_reality_gap(
            candidate(),
            (evidence("evidence-001"), evidence("evidence-002")),
            context(),
            metrics_policy(),
            INPUT_REFS,
        )

        self.assertEqual(classification.analysis_reference, metrics.analysis_reference)
        self.assertEqual(classification.input_references, metrics.input_references)
        self.assertNotEqual(classification.classification_id, metrics.metric_set_id)
        self.assertNotEqual(classification.trace_reference, metrics.trace_reference)

    def test_trace_is_reproducible_and_contains_structured_facts(self):
        output = classify_reality_gap(
            candidate(), context(), classification_policy(), INPUT_REFS
        )
        repeat = classify_reality_gap(
            candidate(), context(), classification_policy(), reversed(INPUT_REFS)
        )
        trace = output.metadata["trace"]

        self.assertEqual(output.trace_reference, repeat.trace_reference)
        self.assertEqual(trace["policy_version"], "classification-v1")
        self.assertEqual(
            trace["produced_output_reference"], output.classification_id
        )
        self.assertEqual(trace["warnings"], ())


if __name__ == "__main__":
    unittest.main()
