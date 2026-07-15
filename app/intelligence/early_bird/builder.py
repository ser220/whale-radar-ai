"""Pure availability-aware construction of Early Bird candidates."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, Iterable, Mapping as TypingMapping, Optional, Tuple

from app.intelligence.early_bird.availability import (
    EarlyBirdFactorValue,
    FactorAvailability,
)
from app.intelligence.early_bird.models import (
    EarlyBirdCandidate,
    _frozen_mapping,
    _mapping_payload,
    _string_tuple,
    _to_plain,
    _unique_references,
    _utc_datetime,
)


CANONICAL_FACTOR_NAMES = (
    "whale_activity",
    "open_interest_change",
    "funding_divergence",
    "volume_expansion",
    "relative_strength",
    "liquidity_event",
    "structure_event",
    "momentum_shift",
)

FACTOR_SCORE_FIELDS = MappingProxyType({
    "whale_activity": "whale_activity_score",
    "open_interest_change": "open_interest_change_score",
    "funding_divergence": "funding_divergence_score",
    "volume_expansion": "volume_expansion_score",
    "relative_strength": "relative_strength_score",
    "liquidity_event": "liquidity_event_score",
    "structure_event": "structure_event_score",
    "momentum_shift": "momentum_shift_score",
})

STRUCTURAL_PLACEHOLDER = 0.0
DEFAULT_AVAILABLE_QUALITY = 50.0
FRESHNESS_WINDOW_SECONDS = 3600.0
CLOSE_TIMESTAMP_WINDOW_SECONDS = 900.0
LOW_COMPLETENESS_THRESHOLD = 50.0


def _ordered_factor_mapping(
    value: Any,
) -> TypingMapping[str, EarlyBirdFactorValue]:
    if not isinstance(value, Mapping):
        raise TypeError("factor_values must be a mapping")

    values = dict(value)
    if set(values) != set(CANONICAL_FACTOR_NAMES):
        raise ValueError("factor_values must contain every canonical factor")

    ordered = {}
    for factor_name in CANONICAL_FACTOR_NAMES:
        factor_value = values[factor_name]
        if not isinstance(factor_value, EarlyBirdFactorValue):
            raise TypeError(
                "factor_values must contain only EarlyBirdFactorValue objects"
            )
        if factor_value.factor_name != factor_name:
            raise ValueError(
                "factor_values key must match the factor value name"
            )
        ordered[factor_name] = factor_value
    return MappingProxyType(ordered)


def _factor_groups(
    factor_values: TypingMapping[str, EarlyBirdFactorValue],
) -> Dict[FactorAvailability, Tuple[str, ...]]:
    return {
        availability: tuple(
            factor_name
            for factor_name in CANONICAL_FACTOR_NAMES
            if factor_values[factor_name].availability is availability
        )
        for availability in FactorAvailability
    }


def _completeness(
    factor_values: TypingMapping[str, EarlyBirdFactorValue],
) -> float:
    expected_supported_count = sum(
        factor_value.availability is not FactorAvailability.UNSUPPORTED
        for factor_value in factor_values.values()
    )
    if expected_supported_count == 0:
        raise ValueError("completeness is undefined when all factors are unsupported")

    available_count = sum(
        factor_value.availability is FactorAvailability.AVAILABLE
        for factor_value in factor_values.values()
    )
    return round(100.0 * available_count / expected_supported_count, 6)


def _quality(
    factor_values: TypingMapping[str, EarlyBirdFactorValue],
) -> float:
    values = tuple(
        (
            factor_value.quality
            if factor_value.quality is not None
            else DEFAULT_AVAILABLE_QUALITY
        )
        for factor_value in factor_values.values()
        if factor_value.availability is FactorAvailability.AVAILABLE
    )
    if not values:
        raise ValueError("at least one AVAILABLE factor is required")
    return round(sum(values) / len(values), 6)


def _available_ages(
    factor_values: TypingMapping[str, EarlyBirdFactorValue],
    observed_at: datetime,
) -> Tuple[float, ...]:
    return tuple(
        max(
            0.0,
            (observed_at - factor_value.observed_at).total_seconds(),
        )
        for factor_value in factor_values.values()
        if factor_value.availability is FactorAvailability.AVAILABLE
    )


def _freshness(ages: Tuple[float, ...]) -> float:
    if not ages:
        raise ValueError("at least one AVAILABLE factor timestamp is required")
    scores = tuple(
        max(
            0.0,
            100.0 - age_seconds / FRESHNESS_WINDOW_SECONDS * 100.0,
        )
        for age_seconds in ages
    )
    return round(min(scores), 6)


def _deduplicate(values: Iterable[str]) -> Tuple[str, ...]:
    result = []
    seen = set()
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return tuple(result)


def _warnings(
    factor_values: TypingMapping[str, EarlyBirdFactorValue],
    completeness: float,
    available_ages: Tuple[float, ...],
) -> Tuple[str, ...]:
    warnings = []
    status_labels = {
        FactorAvailability.MISSING: "missing",
        FactorAvailability.STALE: "stale",
        FactorAvailability.UNSUPPORTED: "unsupported",
        FactorAvailability.ERROR: "in error",
    }

    for factor_name in CANONICAL_FACTOR_NAMES:
        factor_value = factor_values[factor_name]
        if factor_value.availability in status_labels:
            warnings.append(
                "Factor '{0}' is {1}; candidate score uses structural "
                "placeholder 0.0.".format(
                    factor_name,
                    status_labels[factor_value.availability],
                )
            )
        elif factor_value.quality is None:
            warnings.append(
                "Available factor '{0}' has no explicit quality; "
                "quality fallback 50.0 was used.".format(factor_name)
            )

    available_count = sum(
        factor_value.availability is FactorAvailability.AVAILABLE
        for factor_value in factor_values.values()
    )
    if completeness < LOW_COMPLETENESS_THRESHOLD:
        warnings.append(
            "Candidate data completeness is low ({0:.2f}%).".format(
                completeness
            )
        )
    if available_count == 1:
        warnings.append("Only one factor is available.")
    if (
        factor_values["whale_activity"].availability
        is not FactorAvailability.AVAILABLE
    ):
        warnings.append("No whale factor is available.")
    if all(
        age_seconds > CLOSE_TIMESTAMP_WINDOW_SECONDS
        for age_seconds in available_ages
    ):
        warnings.append(
            "No available factor timestamp is within 15 minutes of "
            "the candidate observation time."
        )
    return _deduplicate(warnings)


@dataclass(frozen=True)
class EarlyBirdCandidateBuildResult:
    """Candidate plus immutable factor availability and builder provenance."""

    candidate: EarlyBirdCandidate
    factor_values: TypingMapping[str, EarlyBirdFactorValue]
    available_factors: Tuple[str, ...]
    missing_factors: Tuple[str, ...]
    stale_factors: Tuple[str, ...]
    unsupported_factors: Tuple[str, ...]
    error_factors: Tuple[str, ...]
    warnings: Tuple[str, ...]
    metadata: TypingMapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.candidate, EarlyBirdCandidate):
            raise TypeError("candidate must be an EarlyBirdCandidate")
        factor_values = _ordered_factor_mapping(self.factor_values)
        groups = _factor_groups(factor_values)

        expected_groups = (
            (
                "available_factors",
                FactorAvailability.AVAILABLE,
            ),
            ("missing_factors", FactorAvailability.MISSING),
            ("stale_factors", FactorAvailability.STALE),
            ("unsupported_factors", FactorAvailability.UNSUPPORTED),
            ("error_factors", FactorAvailability.ERROR),
        )
        for field_name, availability in expected_groups:
            normalized = _unique_references(getattr(self, field_name), field_name)
            if normalized != groups[availability]:
                raise ValueError(
                    "{0} must match factor_values availability".format(field_name)
                )
            object.__setattr__(self, field_name, normalized)

        for factor_name, score_field in FACTOR_SCORE_FIELDS.items():
            factor_value = factor_values[factor_name]
            expected_score = (
                factor_value.score
                if factor_value.availability is FactorAvailability.AVAILABLE
                else STRUCTURAL_PLACEHOLDER
            )
            if getattr(self.candidate, score_field) != expected_score:
                raise ValueError(
                    "candidate factor scores must match factor_values"
                )

        if self.candidate.data_completeness_score != _completeness(factor_values):
            raise ValueError(
                "candidate completeness must match factor availability"
            )
        if self.candidate.quality != _quality(factor_values):
            raise ValueError("candidate quality must match AVAILABLE factors")
        ages = _available_ages(factor_values, self.candidate.observed_at)
        if self.candidate.freshness_score != _freshness(ages):
            raise ValueError(
                "candidate freshness must match AVAILABLE timestamps"
            )

        object.__setattr__(self, "factor_values", factor_values)
        normalized_warnings = _string_tuple(self.warnings, "warnings")
        expected_warnings = _warnings(
            factor_values,
            self.candidate.data_completeness_score,
            ages,
        )
        if normalized_warnings != expected_warnings:
            raise ValueError(
                "warnings must match deterministic builder warnings"
            )
        object.__setattr__(self, "warnings", normalized_warnings)
        object.__setattr__(
            self,
            "metadata",
            _frozen_mapping(self.metadata, "metadata"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate": self.candidate.to_dict(),
            "factor_values": {
                factor_name: factor_value.to_dict()
                for factor_name, factor_value in self.factor_values.items()
            },
            "available_factors": list(self.available_factors),
            "missing_factors": list(self.missing_factors),
            "stale_factors": list(self.stale_factors),
            "unsupported_factors": list(self.unsupported_factors),
            "error_factors": list(self.error_factors),
            "warnings": list(self.warnings),
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(
        cls,
        data: TypingMapping[str, Any],
    ) -> "EarlyBirdCandidateBuildResult":
        payload = _mapping_payload(data, "early bird candidate build result")
        payload["candidate"] = EarlyBirdCandidate.from_dict(
            payload.get("candidate")
        )
        raw_factor_values = payload.get("factor_values")
        if not isinstance(raw_factor_values, Mapping):
            raise TypeError("factor_values must be a mapping")
        payload["factor_values"] = {
            factor_name: EarlyBirdFactorValue.from_dict(factor_value)
            for factor_name, factor_value in raw_factor_values.items()
        }
        return cls(**payload)


class EarlyBirdCandidateBuilder:
    """Build candidates from explicit factor values without provider calls."""

    def build(
        self,
        factor_values: Iterable[EarlyBirdFactorValue],
        *,
        candidate_id: str,
        asset: str,
        observed_at: datetime,
        source: str,
        fast_event_ids: Iterable[str] = (),
        observation_ids: Iterable[str] = (),
        metadata: Optional[TypingMapping[str, Any]] = None,
    ) -> EarlyBirdCandidateBuildResult:
        if isinstance(factor_values, (str, bytes)):
            raise TypeError(
                "factor_values must be an iterable of EarlyBirdFactorValue"
            )
        try:
            supplied_values = tuple(factor_values)
        except TypeError as exc:
            raise TypeError(
                "factor_values must be an iterable of EarlyBirdFactorValue"
            ) from exc
        if not supplied_values:
            raise ValueError("factor_values must not be empty")

        supplied_by_name = {}
        for factor_value in supplied_values:
            if not isinstance(factor_value, EarlyBirdFactorValue):
                raise TypeError(
                    "factor_values must contain only EarlyBirdFactorValue objects"
                )
            factor_name = factor_value.factor_name
            if factor_name not in FACTOR_SCORE_FIELDS:
                raise ValueError("unknown factor name: {0}".format(factor_name))
            if factor_name in supplied_by_name:
                raise ValueError("duplicate factor name: {0}".format(factor_name))
            supplied_by_name[factor_name] = factor_value

        synthesized_missing = []
        normalized_values = {}
        for factor_name in CANONICAL_FACTOR_NAMES:
            factor_value = supplied_by_name.get(factor_name)
            if factor_value is None:
                factor_value = EarlyBirdFactorValue(
                    factor_name=factor_name,
                    availability=FactorAvailability.MISSING,
                    reason="No factor value was supplied.",
                )
                synthesized_missing.append(factor_name)
            normalized_values[factor_name] = factor_value
        ordered_values = MappingProxyType(normalized_values)

        expected_supported_count = sum(
            factor_value.availability is not FactorAvailability.UNSUPPORTED
            for factor_value in ordered_values.values()
        )
        if expected_supported_count == 0:
            raise ValueError("all factors are UNSUPPORTED")
        if not any(
            factor_value.availability is FactorAvailability.AVAILABLE
            for factor_value in ordered_values.values()
        ):
            raise ValueError("at least one AVAILABLE factor is required")

        observed_utc = _utc_datetime(observed_at, "observed_at")
        completeness = _completeness(ordered_values)
        quality = _quality(ordered_values)
        ages = _available_ages(ordered_values, observed_utc)
        freshness = _freshness(ages)

        scores = {
            score_field: STRUCTURAL_PLACEHOLDER
            for score_field in FACTOR_SCORE_FIELDS.values()
        }
        for factor_name, factor_value in ordered_values.items():
            if factor_value.availability is FactorAvailability.AVAILABLE:
                scores[FACTOR_SCORE_FIELDS[factor_name]] = factor_value.score

        candidate_metadata = {} if metadata is None else metadata
        candidate = EarlyBirdCandidate(
            candidate_id=candidate_id,
            asset=asset,
            observed_at=observed_utc,
            source=source,
            quality=quality,
            freshness_score=freshness,
            data_completeness_score=completeness,
            fast_event_ids=fast_event_ids,
            observation_ids=observation_ids,
            metadata=candidate_metadata,
            **scores
        )
        groups = _factor_groups(ordered_values)
        warnings = _warnings(ordered_values, completeness, ages)
        result_metadata = {
            "builder_policy": {
                "structural_placeholder": STRUCTURAL_PLACEHOLDER,
                "available_quality_fallback": DEFAULT_AVAILABLE_QUALITY,
                "freshness_window_seconds": FRESHNESS_WINDOW_SECONDS,
                "close_timestamp_window_seconds": (
                    CLOSE_TIMESTAMP_WINDOW_SECONDS
                ),
                "completeness_excludes": [
                    FactorAvailability.UNSUPPORTED.value
                ],
                "quality_uses": [FactorAvailability.AVAILABLE.value],
            },
            "candidate_metadata": candidate_metadata,
            "synthesized_missing_factors": synthesized_missing,
        }

        return EarlyBirdCandidateBuildResult(
            candidate=candidate,
            factor_values=ordered_values,
            available_factors=groups[FactorAvailability.AVAILABLE],
            missing_factors=groups[FactorAvailability.MISSING],
            stale_factors=groups[FactorAvailability.STALE],
            unsupported_factors=groups[FactorAvailability.UNSUPPORTED],
            error_factors=groups[FactorAvailability.ERROR],
            warnings=warnings,
            metadata=result_metadata,
        )
