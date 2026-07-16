"""Pure read-only Classification and Metrics consumers."""

from collections.abc import Mapping
import hashlib
from typing import Iterable, Tuple

from app.intelligence.reality_gap.enums import RealityGapEvidenceEligibility
from app.intelligence.reality_gap.models import (
    RealityGapEvidenceReference,
    RootCauseCandidate,
)

from ._validation import canonical_json_bytes, ordered_references
from .consumer_enums import (
    ClassificationConsumerFailureCategory,
    MetricIndicator,
    MetricsConsumerFailureCategory,
)
from .consumer_models import (
    ClassificationConsumerError,
    ClassificationConsumerPolicy,
    MetricsConsumerError,
    MetricsConsumerPolicy,
    RealityGapConsumerContext,
)
from .enums import MetricAvailability
from .models import (
    RealityGapClassification,
    RealityGapMetricSet,
    RealityGapMetricValue,
)


def _stable_reference(prefix: str, payload: dict) -> str:
    digest = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    return "{0}-{1}".format(prefix, digest[:24])


def _classification_input_error(field_name: str, reason: str) -> ValueError:
    return ClassificationConsumerError(
        ClassificationConsumerFailureCategory.INVALID_INPUT_REFERENCE,
        field_name,
        reason,
    )


def _metrics_input_error(field_name: str, reason: str) -> ValueError:
    return MetricsConsumerError(
        MetricsConsumerFailureCategory.INVALID_INPUT_REFERENCE,
        field_name,
        reason,
    )


def _validated_input_references(
    value: Iterable[str],
    candidate: RootCauseCandidate,
    context: RealityGapConsumerContext,
    metrics: bool,
) -> Tuple[str, ...]:
    error = _metrics_input_error if metrics else _classification_input_error
    references = ordered_references(value, "input_references", error)
    if candidate.candidate_id not in references:
        raise error("input_references", "must include the candidate reference")
    allowed = set(context.candidate_references) | set(context.evidence_references)
    if not set(references) <= allowed:
        raise error("input_references", "contains a reference outside the context")
    return references


def _validate_common(
    candidate: RootCauseCandidate,
    context: RealityGapConsumerContext,
    expected_candidate_policy_version: str,
    expected_analysis_policy_version: str,
    metrics: bool,
) -> None:
    error_type = MetricsConsumerError if metrics else ClassificationConsumerError
    input_category = (
        MetricsConsumerFailureCategory.INVALID_INPUT_REFERENCE
        if metrics
        else ClassificationConsumerFailureCategory.INVALID_INPUT_REFERENCE
    )
    version_category = (
        MetricsConsumerFailureCategory.VERSION_CONFLICT
        if metrics
        else ClassificationConsumerFailureCategory.VERSION_CONFLICT
    )
    if not isinstance(candidate, RootCauseCandidate):
        raise error_type(input_category, "candidate", "must be a RootCauseCandidate")
    if not isinstance(context, RealityGapConsumerContext):
        raise error_type(
            input_category,
            "context",
            "must be a RealityGapConsumerContext",
        )
    if candidate.candidate_id not in context.candidate_references:
        raise error_type(
            input_category,
            "candidate",
            "candidate is not approved by the historical context",
        )
    if candidate.policy_version != expected_candidate_policy_version:
        raise error_type(
            version_category,
            "candidate.policy_version",
            "does not match the consumer policy",
        )
    if context.analysis_policy_version != expected_analysis_policy_version:
        raise error_type(
            version_category,
            "context.analysis_policy_version",
            "does not match the consumer policy",
        )


def classify_reality_gap(
    candidate: RootCauseCandidate,
    context: RealityGapConsumerContext,
    policy: ClassificationConsumerPolicy,
    input_references: Iterable[str],
) -> RealityGapClassification:
    """Apply an explicit policy mapping without inference, I/O, or mutation."""

    if not isinstance(policy, ClassificationConsumerPolicy):
        raise ClassificationConsumerError(
            ClassificationConsumerFailureCategory.POLICY_MISMATCH,
            "policy",
            "must be a ClassificationConsumerPolicy",
        )
    _validate_common(
        candidate,
        context,
        policy.expected_candidate_policy_version,
        policy.expected_analysis_policy_version,
        False,
    )
    references = _validated_input_references(
        input_references, candidate, context, False
    )
    assignment = policy.assignments.get(candidate.category)
    if assignment is None:
        raise ClassificationConsumerError(
            ClassificationConsumerFailureCategory.UNSUPPORTED_DIMENSION,
            "candidate.category",
            "the approved policy has no explicit assignment",
        )

    identity_payload = {
        "analysis_reference": context.analysis_reference,
        "analysis_version": context.analysis_version,
        "candidate_id": candidate.candidate_id,
        "candidate_policy_version": candidate.policy_version,
        "classification_policy_version": policy.policy_version,
        "input_references": list(references),
        "dimensions": [item.value for item in assignment.dimensions],
        "categories": list(assignment.categories),
        "evaluated_at": context.evaluated_at.isoformat(),
    }
    classification_id = _stable_reference("classification", identity_payload)
    trace_payload = {
        "input_references": list(references),
        "policy_version": policy.policy_version,
        "produced_output_reference": classification_id,
        "warnings": [],
    }
    trace_reference = _stable_reference("classification-trace", trace_payload)
    metadata = {
        "candidate_reference": candidate.candidate_id,
        "candidate_category": candidate.category.value,
        "analysis_version": context.analysis_version,
        "historical_boundary": context.evaluated_at.isoformat(),
        "trace": trace_payload,
    }
    return RealityGapClassification(
        classification_id=classification_id,
        classification_policy_version=policy.policy_version,
        analysis_reference=context.analysis_reference,
        input_references=references,
        dimensions=assignment.dimensions,
        categories=assignment.categories,
        created_at=context.evaluated_at,
        trace_reference=trace_reference,
        metadata=metadata,
    )


def _availability_from_evidence(
    evidence: Tuple[RealityGapEvidenceReference, ...],
) -> Tuple[MetricAvailability, object, Tuple[str, ...]]:
    if not evidence:
        return MetricAvailability.MISSING, None, ("no evidence records resolved",)
    statuses = tuple(
        "UNAVAILABLE" if item.availability is None else item.availability.upper()
        for item in evidence
    )
    allowed = {item.value for item in MetricAvailability}
    if any(status not in allowed for status in statuses):
        raise _metrics_input_error(
            "evidence.availability", "contains an unsupported availability state"
        )
    available_count = statuses.count(MetricAvailability.AVAILABLE.value)
    if available_count:
        value = round((available_count / len(statuses)) * 100.0, 12)
        warnings = (
            ()
            if available_count == len(statuses)
            else ("some evidence records are not AVAILABLE",)
        )
        return MetricAvailability.AVAILABLE, value, warnings
    unique = set(statuses)
    if len(unique) == 1:
        return MetricAvailability(next(iter(unique))), None, (
            "no evidence record is AVAILABLE",
        )
    return MetricAvailability.UNAVAILABLE, None, (
        "evidence availability states are mixed and none is AVAILABLE",
    )


def measure_reality_gap(
    candidate: RootCauseCandidate,
    evidence_references: Iterable[RealityGapEvidenceReference],
    context: RealityGapConsumerContext,
    policy: MetricsConsumerPolicy,
    input_references: Iterable[str],
) -> RealityGapMetricSet:
    """Measure two explicit ratios from historical references only."""

    if not isinstance(policy, MetricsConsumerPolicy):
        raise MetricsConsumerError(
            MetricsConsumerFailureCategory.POLICY_MISMATCH,
            "policy",
            "must be a MetricsConsumerPolicy",
        )
    _validate_common(
        candidate,
        context,
        policy.expected_candidate_policy_version,
        policy.expected_analysis_policy_version,
        True,
    )
    references = _validated_input_references(
        input_references, candidate, context, True
    )
    if isinstance(evidence_references, (str, bytes, set, frozenset, Mapping)):
        raise _metrics_input_error(
            "evidence_references", "must be an ordered collection"
        )
    try:
        evidence = tuple(evidence_references)
    except TypeError:
        raise _metrics_input_error(
            "evidence_references", "must be an ordered collection"
        )
    if any(not isinstance(item, RealityGapEvidenceReference) for item in evidence):
        raise _metrics_input_error(
            "evidence_references",
            "must contain RealityGapEvidenceReference objects",
        )
    ids = tuple(item.evidence_id for item in evidence)
    if len(set(ids)) != len(ids):
        raise _metrics_input_error(
            "evidence_references", "must not contain duplicate evidence IDs"
        )
    expected_ids = set(candidate.supporting_evidence_refs) | set(
        candidate.contradicting_evidence_refs
    )
    if not set(ids) <= expected_ids:
        raise _metrics_input_error(
            "evidence_references", "contains evidence unrelated to the candidate"
        )
    if not set(expected_ids) <= set(context.evidence_references):
        raise _metrics_input_error(
            "context.evidence_references",
            "does not approve every candidate evidence reference",
        )
    if not ({candidate.candidate_id} | expected_ids) <= set(references):
        raise _metrics_input_error(
            "input_references",
            "must declare candidate and expected evidence lineage",
        )
    for item in evidence:
        if item.eligibility is not RealityGapEvidenceEligibility.ELIGIBLE:
            raise _metrics_input_error(
                "evidence_references", "must contain approved ELIGIBLE evidence"
            )
        if not (
            context.eligible_window_start
            <= item.observed_at
            <= context.eligible_window_end
            <= context.evaluated_at
        ):
            raise _metrics_input_error(
                "evidence_references",
                "contains future or out-of-window evidence",
            )
    evidence = tuple(sorted(evidence, key=lambda item: item.evidence_id))

    metrics = {}
    warnings = []
    for indicator in policy.indicators:
        if indicator is MetricIndicator.REFERENCE_COVERAGE:
            if not expected_ids:
                metric = RealityGapMetricValue(
                    availability=MetricAvailability.UNAVAILABLE,
                    value=None,
                    unit="percent",
                    policy_reference="{0}:{1}".format(
                        policy.policy_version, indicator.value
                    ),
                    metadata={"reason": "candidate has no evidence references"},
                )
                warnings.append("reference coverage unavailable: no expected references")
            else:
                coverage = round((len(evidence) / len(expected_ids)) * 100.0, 12)
                metric = RealityGapMetricValue(
                    availability=MetricAvailability.AVAILABLE,
                    value=coverage,
                    unit="percent",
                    policy_reference="{0}:{1}".format(
                        policy.policy_version, indicator.value
                    ),
                    metadata={
                        "resolved_reference_count": len(evidence),
                        "expected_reference_count": len(expected_ids),
                    },
                )
        elif indicator is MetricIndicator.EVIDENCE_AVAILABILITY_RATIO:
            availability, value, indicator_warnings = _availability_from_evidence(
                evidence
            )
            warnings.extend(indicator_warnings)
            metric = RealityGapMetricValue(
                availability=availability,
                value=value,
                unit="percent",
                policy_reference="{0}:{1}".format(
                    policy.policy_version, indicator.value
                ),
                metadata={"evidence_count": len(evidence)},
            )
        else:
            raise MetricsConsumerError(
                MetricsConsumerFailureCategory.UNSUPPORTED_METRIC,
                "policy.indicators",
                "contains an unsupported metric",
            )
        metrics[indicator.value] = metric

    identity_payload = {
        "analysis_reference": context.analysis_reference,
        "analysis_version": context.analysis_version,
        "candidate_id": candidate.candidate_id,
        "candidate_policy_version": candidate.policy_version,
        "metric_policy_version": policy.policy_version,
        "input_references": list(references),
        "evidence_references": [item.to_dict() for item in evidence],
        "indicators": [item.value for item in policy.indicators],
        "evaluated_at": context.evaluated_at.isoformat(),
    }
    metric_set_id = _stable_reference("metric-set", identity_payload)
    trace_payload = {
        "input_references": list(references),
        "policy_version": policy.policy_version,
        "produced_output_reference": metric_set_id,
        "warnings": sorted(set(warnings)),
    }
    trace_reference = _stable_reference("metric-trace", trace_payload)
    metadata = {
        "candidate_reference": candidate.candidate_id,
        "analysis_version": context.analysis_version,
        "historical_boundary": context.evaluated_at.isoformat(),
        "trace": trace_payload,
    }
    return RealityGapMetricSet(
        metric_set_id=metric_set_id,
        metric_policy_version=policy.policy_version,
        analysis_reference=context.analysis_reference,
        input_references=references,
        metrics=metrics,
        created_at=context.evaluated_at,
        trace_reference=trace_reference,
        metadata=metadata,
    )


__all__ = ["classify_reality_gap", "measure_reality_gap"]
