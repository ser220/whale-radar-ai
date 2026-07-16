"""Focused tests for immutable Classification and Metrics contracts."""

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
import json
import unittest

from app.intelligence.classification_metrics import (
    ClassificationFailureCategory,
    ClassificationValidationError,
    MetricAvailability,
    MetricFailureCategory,
    MetricValidationError,
    RealityGapClassification,
    RealityGapMetricSet,
    RealityGapMetricValue,
)
from app.intelligence.reality_gap.enums import RealityGapDimension


UTC_TIME = datetime(2026, 7, 16, 9, 0, tzinfo=timezone.utc)


def classification(**overrides):
    values = {
        "classification_id": "classification-001",
        "classification_policy_version": "classification-v1",
        "analysis_reference": "analysis-001:v3",
        "input_references": ("root-cause-b:v1", "root-cause-a:v2"),
        "dimensions": (
            RealityGapDimension.OBSERVABILITY,
            RealityGapDimension.MARKET,
        ),
        "categories": ("MIXED_GAP", "OBSERVABILITY_GAP"),
        "created_at": UTC_TIME,
        "trace_reference": "classification-trace-001:v1",
        "metadata": {"lineage": {"mapping": "mapping-001:v2"}},
    }
    values.update(overrides)
    return RealityGapClassification(**values)


def metric_value(**overrides):
    values = {
        "availability": MetricAvailability.AVAILABLE,
        "value": 75.0,
        "unit": "percent",
        "policy_reference": "coverage-v1",
        "metadata": {"source": ["evidence-a", "evidence-b"]},
    }
    values.update(overrides)
    return RealityGapMetricValue(**values)


def metric_set(**overrides):
    values = {
        "metric_set_id": "metric-set-001",
        "metric_policy_version": "metrics-v1",
        "analysis_reference": "analysis-001:v3",
        "input_references": ("root-cause-b:v1", "root-cause-a:v2"),
        "metrics": {
            "observability": metric_value(value=80.0),
            "evidence_coverage": metric_value(value=70.0),
        },
        "created_at": UTC_TIME,
        "trace_reference": "metric-trace-001:v1",
        "metadata": {"lineage": {"analysis": "analysis-001:v3"}},
    }
    values.update(overrides)
    return RealityGapMetricSet(**values)


class RealityGapClassificationTests(unittest.TestCase):
    def test_immutable_construction_and_defensive_conversion(self):
        source_metadata = {"nested": {"items": ["a", "b"]}}
        value = classification(metadata=source_metadata)
        source_metadata["nested"]["items"].append("later")

        self.assertEqual(value.input_references, ("root-cause-a:v2", "root-cause-b:v1"))
        self.assertEqual(
            value.dimensions,
            (RealityGapDimension.MARKET, RealityGapDimension.OBSERVABILITY),
        )
        self.assertEqual(value.metadata["nested"]["items"], ("a", "b"))
        with self.assertRaises(TypeError):
            value.metadata["new"] = "mutation"
        with self.assertRaises(FrozenInstanceError):
            value.classification_id = "other"

    def test_serialization_round_trip_preserves_enums_and_timestamp(self):
        value = classification()
        restored = RealityGapClassification.from_dict(value.to_dict())

        self.assertEqual(restored, value)
        self.assertIsInstance(restored.dimensions[0], RealityGapDimension)
        self.assertEqual(restored.created_at.tzinfo, timezone.utc)

    def test_canonical_bytes_are_deterministic_and_valid_json(self):
        first = classification(
            input_references=("b", "a"),
            categories=("OBSERVABILITY_GAP", "MIXED_GAP"),
            metadata={"z": 1, "a": {"y": 2, "x": 3}},
        )
        second = classification(
            input_references=("a", "b"),
            categories=("MIXED_GAP", "OBSERVABILITY_GAP"),
            metadata={"a": {"x": 3, "y": 2}, "z": 1},
        )

        self.assertEqual(first, second)
        self.assertEqual(first.to_json_bytes(), second.to_json_bytes())
        self.assertEqual(
            json.loads(first.to_json_bytes().decode("utf-8")),
            first.to_dict(),
        )

    def test_dimension_validation_rejects_unknown_and_duplicates(self):
        for dimensions in (
            (RealityGapDimension.UNKNOWN,),
            ("FUTURE_DIMENSION",),
            (RealityGapDimension.MARKET, RealityGapDimension.MARKET),
            (),
        ):
            with self.subTest(dimensions=dimensions):
                with self.assertRaises(ClassificationValidationError) as caught:
                    classification(dimensions=dimensions)
                self.assertEqual(
                    caught.exception.category,
                    ClassificationFailureCategory.INVALID_DIMENSION,
                )

    def test_category_validation_requires_canonical_tokens(self):
        for categories in ((), ("lowercase",), ("HAS SPACE",), ("MARKET", "MARKET")):
            with self.subTest(categories=categories):
                with self.assertRaises(ClassificationValidationError) as caught:
                    classification(categories=categories)
                self.assertEqual(
                    caught.exception.category,
                    ClassificationFailureCategory.INVALID_CATEGORY,
                )

    def test_timestamp_validation_and_utc_normalization(self):
        with self.assertRaises(ClassificationValidationError) as caught:
            classification(created_at=datetime(2026, 7, 16, 9, 0))
        self.assertEqual(
            caught.exception.category,
            ClassificationFailureCategory.INVALID_TIMESTAMP,
        )

        offset = timezone(timedelta(hours=3))
        value = classification(created_at=datetime(2026, 7, 16, 12, 0, tzinfo=offset))
        self.assertEqual(value.created_at, UTC_TIME)
        self.assertEqual(value.created_at.tzinfo, timezone.utc)

    def test_identity_policy_analysis_and_payload_failures_are_categorized(self):
        cases = (
            (
                {"classification_id": " "},
                ClassificationFailureCategory.MISSING_IDENTITY,
            ),
            (
                {"classification_policy_version": "bad version"},
                ClassificationFailureCategory.INVALID_POLICY_VERSION,
            ),
            (
                {"analysis_reference": ""},
                ClassificationFailureCategory.INVALID_ANALYSIS_REFERENCE,
            ),
            (
                {"metadata": {"bad": {"unordered"}}},
                ClassificationFailureCategory.MUTABLE_PAYLOAD,
            ),
        )
        for overrides, expected in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ClassificationValidationError) as caught:
                    classification(**overrides)
                self.assertEqual(caught.exception.category, expected)

    def test_identity_separation_is_enforced(self):
        with self.assertRaises(ClassificationValidationError) as caught:
            classification(classification_id="analysis-001:v3")
        self.assertEqual(
            caught.exception.category,
            ClassificationFailureCategory.MISSING_IDENTITY,
        )


class RealityGapMetricsTests(unittest.TestCase):
    def test_immutable_construction_and_deterministic_metric_order(self):
        source_metrics = {
            "observability": metric_value(value=80.0),
            "evidence_coverage": metric_value(value=70.0),
        }
        value = metric_set(metrics=source_metrics)
        source_metrics["later"] = metric_value(value=1.0)

        self.assertEqual(tuple(value.metrics), ("evidence_coverage", "observability"))
        with self.assertRaises(TypeError):
            value.metrics["new"] = metric_value()
        with self.assertRaises(FrozenInstanceError):
            value.metric_set_id = "other"

    def test_serialization_round_trip(self):
        value = metric_set()
        restored = RealityGapMetricSet.from_dict(value.to_dict())

        self.assertEqual(restored, value)
        self.assertIsInstance(
            restored.metrics["observability"].availability,
            MetricAvailability,
        )
        self.assertEqual(restored.created_at.tzinfo, timezone.utc)

    def test_canonical_bytes_are_stable_across_input_order(self):
        first = metric_set(
            input_references=("b", "a"),
            metrics={
                "observability": metric_value(value=80.0),
                "evidence_coverage": metric_value(value=70.0),
            },
            metadata={"z": 1, "a": [2, 3]},
        )
        second = metric_set(
            input_references=("a", "b"),
            metrics={
                "evidence_coverage": metric_value(value=70.0),
                "observability": metric_value(value=80.0),
            },
            metadata={"a": [2, 3], "z": 1},
        )

        self.assertEqual(first, second)
        self.assertEqual(first.to_json_bytes(), second.to_json_bytes())

    def test_metric_key_and_value_validation(self):
        invalid_metrics = (
            {},
            {"HasCaps": metric_value()},
            {"has space": metric_value()},
            {"valid": object()},
        )
        for metrics in invalid_metrics:
            with self.subTest(metrics=metrics):
                with self.assertRaises(MetricValidationError) as caught:
                    metric_set(metrics=metrics)
                self.assertEqual(
                    caught.exception.category,
                    MetricFailureCategory.INVALID_METRIC,
                )

    def test_available_requires_finite_numeric_value(self):
        for value in (None, True, float("inf"), "75"):
            with self.subTest(value=value):
                with self.assertRaises(MetricValidationError):
                    metric_value(value=value)

    def test_non_available_states_are_distinct_and_never_zero_filled(self):
        states = (
            MetricAvailability.MISSING,
            MetricAvailability.STALE,
            MetricAvailability.UNSUPPORTED,
            MetricAvailability.UNAVAILABLE,
            MetricAvailability.ERROR,
        )
        values = tuple(
            metric_value(availability=state, value=None, unit=None) for state in states
        )

        self.assertEqual(tuple(item.availability for item in values), states)
        self.assertTrue(all(item.value is None for item in values))
        self.assertEqual(
            {item.to_dict()["availability"] for item in values},
            {item.value for item in states},
        )

    def test_non_available_value_is_rejected_including_zero(self):
        for state in (
            MetricAvailability.MISSING,
            MetricAvailability.UNSUPPORTED,
            MetricAvailability.UNAVAILABLE,
            MetricAvailability.ERROR,
        ):
            with self.subTest(state=state):
                with self.assertRaises(MetricValidationError) as caught:
                    metric_value(availability=state, value=0)
                self.assertEqual(
                    caught.exception.category,
                    MetricFailureCategory.INVALID_AVAILABILITY,
                )

    def test_invalid_availability_is_categorized(self):
        with self.assertRaises(MetricValidationError) as caught:
            metric_value(availability="FAILED", value=None)
        self.assertEqual(
            caught.exception.category,
            MetricFailureCategory.INVALID_AVAILABILITY,
        )

    def test_metric_set_validation_categories(self):
        cases = (
            ({"metric_set_id": ""}, MetricFailureCategory.MISSING_IDENTITY),
            (
                {"metric_policy_version": "bad version"},
                MetricFailureCategory.INVALID_POLICY_VERSION,
            ),
            (
                {"analysis_reference": ""},
                MetricFailureCategory.INVALID_ANALYSIS_REFERENCE,
            ),
            (
                {"created_at": datetime(2026, 7, 16, 9, 0)},
                MetricFailureCategory.INVALID_TIMESTAMP,
            ),
            (
                {"metadata": {"bad": {"unordered"}}},
                MetricFailureCategory.MUTABLE_PAYLOAD,
            ),
        )
        for overrides, expected in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(MetricValidationError) as caught:
                    metric_set(**overrides)
                self.assertEqual(caught.exception.category, expected)

    def test_metric_value_metadata_is_deeply_frozen(self):
        source = {"nested": {"items": [1, 2]}}
        value = metric_value(metadata=source)
        source["nested"]["items"].append(3)

        self.assertEqual(value.metadata["nested"]["items"], (1, 2))
        with self.assertRaises(TypeError):
            value.metadata["x"] = 1


class ContractIntegrationBoundaryTests(unittest.TestCase):
    def test_lineage_is_preserved_without_identity_collapse(self):
        classification_value = classification()
        metric_value_set = metric_set()

        self.assertEqual(
            classification_value.analysis_reference,
            metric_value_set.analysis_reference,
        )
        self.assertEqual(
            classification_value.input_references,
            metric_value_set.input_references,
        )
        self.assertNotEqual(
            classification_value.classification_id,
            metric_value_set.metric_set_id,
        )
        self.assertNotEqual(
            classification_value.classification_policy_version,
            metric_value_set.metric_policy_version,
        )

    def test_contracts_contain_no_decision_or_trade_fields(self):
        forbidden = {
            "action",
            "buy",
            "confidence",
            "direction",
            "rank",
            "recommendation",
            "sell",
            "severity",
            "signal",
        }
        for model in (
            RealityGapClassification,
            RealityGapMetricValue,
            RealityGapMetricSet,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(forbidden.isdisjoint(item.name for item in fields(model)))


if __name__ == "__main__":
    unittest.main()
