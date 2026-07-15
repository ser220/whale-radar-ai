"""Deterministic descriptive classification of forming Early Bird situations."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Iterable, Mapping as TypingMapping, Optional, Tuple

from app.intelligence.early_bird.availability import FactorAvailability
from app.intelligence.early_bird.builder import (
    CANONICAL_FACTOR_NAMES,
    EarlyBirdCandidateBuildResult,
)
from app.intelligence.early_bird.explain import (
    EarlyBirdExplanation,
    FACTOR_LABELS,
)
from app.intelligence.early_bird.models import (
    EarlyBirdAssessment,
    _frozen_mapping,
    _mapping_payload,
    _parse_datetime,
    _percentage,
    _required_text,
    _string_tuple,
    _to_plain,
    _utc_datetime,
)


class EmergingStage(str, Enum):
    """Descriptive development stage without trade or direction semantics."""

    UNKNOWN = "UNKNOWN"
    SEED = "SEED"
    EMERGING = "EMERGING"
    BUILDING = "BUILDING"
    MATURE = "MATURE"
    EXHAUSTED = "EXHAUSTED"


EMERGENCE_FACTOR_WEIGHTS = MappingProxyType({
    "whale_activity": 0.25,
    "funding_divergence": 0.20,
    "volume_expansion": 0.20,
    "structure_event": 0.20,
    "momentum_shift": 0.15,
})
INITIATING_FACTORS = (
    "whale_activity",
    "funding_divergence",
    "structure_event",
)
CONFIRMATION_FACTORS = (
    "momentum_shift",
    "volume_expansion",
)
ACTIVE_FACTOR_THRESHOLD = 25.0
CONFIRMATION_THRESHOLD = 40.0
LOW_COMPLETENESS_THRESHOLD = 60.0
LOW_QUALITY_THRESHOLD = 50.0
LOW_DETECTION_CONFIDENCE = 50.0
UNKNOWN_DETECTION_CONFIDENCE = 20.0
EMERGING_VERSION = 1


def _bounded(value: float) -> float:
    return round(min(100.0, max(0.0, float(value))), 6)


def _stage(value: Any) -> EmergingStage:
    if isinstance(value, EmergingStage):
        return value
    try:
        return EmergingStage(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid emerging stage: {0!r}".format(value)) from exc


def _deduplicate(values: Iterable[str]) -> Tuple[str, ...]:
    result = []
    seen = set()
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return tuple(result)


def _label(factor_name: str) -> str:
    return FACTOR_LABELS.get(
        factor_name,
        factor_name.replace("_", " ").title(),
    )


@dataclass(frozen=True)
class EmergingSituation:
    """Immutable output describing whether a situation is still forming."""

    asset: str
    evaluated_at: datetime
    emergence_score: float
    horizon_score: float
    detection_confidence: float
    stage: EmergingStage
    supporting_factors: Tuple[str, ...]
    limiting_factors: Tuple[str, ...]
    missing_factors: Tuple[str, ...]
    stale_factors: Tuple[str, ...]
    unsupported_factors: Tuple[str, ...]
    error_factors: Tuple[str, ...]
    reasons: Tuple[str, ...]
    warnings: Tuple[str, ...]
    source_assessment_id: str
    source_candidate_id: str
    metadata: TypingMapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "asset",
            _required_text(self.asset, "asset").upper(),
        )
        object.__setattr__(
            self,
            "evaluated_at",
            _utc_datetime(self.evaluated_at, "evaluated_at"),
        )
        for field_name in (
            "emergence_score",
            "horizon_score",
            "detection_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _percentage(getattr(self, field_name), field_name),
            )
        object.__setattr__(self, "stage", _stage(self.stage))
        for field_name in (
            "supporting_factors",
            "limiting_factors",
            "missing_factors",
            "stale_factors",
            "unsupported_factors",
            "error_factors",
            "reasons",
            "warnings",
        ):
            object.__setattr__(
                self,
                field_name,
                _string_tuple(getattr(self, field_name), field_name),
            )
        availability_count = sum(
            len(getattr(self, field_name))
            for field_name in (
                "missing_factors",
                "stale_factors",
                "unsupported_factors",
                "error_factors",
            )
        )
        availability_union = set(self.missing_factors)
        availability_union.update(self.stale_factors)
        availability_union.update(self.unsupported_factors)
        availability_union.update(self.error_factors)
        if len(availability_union) != availability_count:
            raise ValueError("factor availability groups must not overlap")
        if set(self.supporting_factors) & availability_union:
            raise ValueError("supporting factors must be AVAILABLE")
        if not self.reasons:
            raise ValueError("reasons must not be empty")
        object.__setattr__(
            self,
            "source_assessment_id",
            _required_text(self.source_assessment_id, "source_assessment_id"),
        )
        object.__setattr__(
            self,
            "source_candidate_id",
            _required_text(self.source_candidate_id, "source_candidate_id"),
        )
        object.__setattr__(
            self,
            "metadata",
            _frozen_mapping(self.metadata, "metadata"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "evaluated_at": self.evaluated_at.isoformat(),
            "emergence_score": self.emergence_score,
            "horizon_score": self.horizon_score,
            "detection_confidence": self.detection_confidence,
            "stage": self.stage.value,
            "supporting_factors": list(self.supporting_factors),
            "limiting_factors": list(self.limiting_factors),
            "missing_factors": list(self.missing_factors),
            "stale_factors": list(self.stale_factors),
            "unsupported_factors": list(self.unsupported_factors),
            "error_factors": list(self.error_factors),
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "source_assessment_id": self.source_assessment_id,
            "source_candidate_id": self.source_candidate_id,
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(
        cls,
        data: TypingMapping[str, Any],
    ) -> "EmergingSituation":
        payload = _mapping_payload(data, "emerging situation")
        payload["evaluated_at"] = _parse_datetime(
            payload.get("evaluated_at"),
            "evaluated_at",
        )
        payload["stage"] = _stage(payload.get("stage"))
        return cls(**payload)


class EmergingSituationEngine:
    """Evaluate forming-state evidence without decisions or provider calls."""

    def evaluate(
        self,
        assessment: EarlyBirdAssessment,
        build_result: EarlyBirdCandidateBuildResult,
        explanation: EarlyBirdExplanation,
        *,
        timestamp: Optional[datetime] = None,
    ) -> EmergingSituation:
        self._validate_inputs(assessment, build_result, explanation)
        evaluated_at = (
            assessment.evaluated_at
            if timestamp is None
            else _utc_datetime(timestamp, "timestamp")
        )
        factor_values = build_result.factor_values
        available_emergence = tuple(
            factor_name
            for factor_name in EMERGENCE_FACTOR_WEIGHTS
            if factor_values[factor_name].availability
            is FactorAvailability.AVAILABLE
        )
        fresh_strength = self._fresh_factor_strength(
            available_emergence,
            factor_values,
        )
        active_emergence = tuple(
            factor_name
            for factor_name in available_emergence
            if factor_values[factor_name].score >= ACTIVE_FACTOR_THRESHOLD
        )
        independence_proxy = self._independence_proxy(len(active_emergence))

        if available_emergence:
            emergence = _bounded(
                0.55 * fresh_strength
                + 0.20 * assessment.opportunity_score
                + 0.15 * build_result.candidate.freshness_score
                + 0.10 * independence_proxy
            )
        else:
            emergence = 0.0

        early_structure = self._early_structure_proxy(build_result)
        incomplete_confirmation = self._incomplete_confirmation_proxy(
            build_result
        )
        horizon = _bounded(
            0.50 * (100.0 - assessment.maturity_score)
            + 0.20 * build_result.candidate.freshness_score
            + 0.20 * early_structure
            + 0.10 * incomplete_confirmation
        )
        active_supported_count, supported_expected_count = (
            self._independent_factor_counts(build_result)
        )
        independent_coverage = (
            active_supported_count / supported_expected_count * 100.0
            if supported_expected_count
            else 0.0
        )
        confidence = _bounded(
            0.40 * build_result.candidate.data_completeness_score
            + 0.30 * build_result.candidate.quality
            + 0.20 * independent_coverage
            + 0.10 * build_result.candidate.freshness_score
        )
        stage = self._development_stage(
            emergence=emergence,
            horizon=horizon,
            maturity=assessment.maturity_score,
            detection_confidence=confidence,
            has_emergence_factors=bool(available_emergence),
            warnings=explanation.warnings,
        )
        supporting = self._supporting_factors(build_result, explanation)
        limiting = self._limiting_factors(
            assessment,
            build_result,
            active_emergence,
        )
        reasons = self._reasons(
            assessment,
            build_result,
            supporting,
            active_emergence,
        )
        warnings = self._warnings(
            assessment,
            build_result,
            explanation,
            confidence=confidence,
            horizon=horizon,
            available_emergence=available_emergence,
            active_emergence=active_emergence,
        )

        return EmergingSituation(
            asset=assessment.asset,
            evaluated_at=evaluated_at,
            emergence_score=emergence,
            horizon_score=horizon,
            detection_confidence=confidence,
            stage=stage,
            supporting_factors=supporting,
            limiting_factors=limiting,
            missing_factors=build_result.missing_factors,
            stale_factors=build_result.stale_factors,
            unsupported_factors=build_result.unsupported_factors,
            error_factors=build_result.error_factors,
            reasons=reasons,
            warnings=warnings,
            source_assessment_id=assessment.assessment_id,
            source_candidate_id=assessment.candidate_id,
            metadata={
                "emerging_version": EMERGING_VERSION,
                "fresh_factor_strength": fresh_strength,
                "independence_proxy": independence_proxy,
                "active_emergence_factors": list(active_emergence),
                "available_emergence_factors": list(available_emergence),
                "early_structure_proxy": early_structure,
                "incomplete_confirmation_proxy": incomplete_confirmation,
                "independent_factor_coverage": round(
                    independent_coverage,
                    6,
                ),
                "active_supported_factor_count": active_supported_count,
                "supported_expected_factor_count": supported_expected_count,
                "source_opportunity_score": assessment.opportunity_score,
                "source_priority_score": assessment.priority_score,
                "source_maturity_score": assessment.maturity_score,
                "active_factor_threshold": ACTIVE_FACTOR_THRESHOLD,
                "confirmation_threshold": CONFIRMATION_THRESHOLD,
            },
        )

    @staticmethod
    def _validate_inputs(
        assessment: Any,
        build_result: Any,
        explanation: Any,
    ) -> None:
        if not isinstance(assessment, EarlyBirdAssessment):
            raise TypeError("assessment must be an EarlyBirdAssessment")
        if not isinstance(build_result, EarlyBirdCandidateBuildResult):
            raise TypeError(
                "build_result must be an EarlyBirdCandidateBuildResult"
            )
        if not isinstance(explanation, EarlyBirdExplanation):
            raise TypeError("explanation must be an EarlyBirdExplanation")
        candidate = build_result.candidate
        if assessment.candidate_id != candidate.candidate_id:
            raise ValueError("assessment and build result candidate IDs must match")
        if assessment.asset != candidate.asset:
            raise ValueError("assessment and build result assets must match")
        if explanation.asset != assessment.asset:
            raise ValueError("explanation and assessment assets must match")
        if explanation.opportunity_score != assessment.opportunity_score:
            raise ValueError("explanation opportunity score must match assessment")
        if explanation.priority_score != assessment.priority_score:
            raise ValueError("explanation priority score must match assessment")
        if explanation.maturity_score != assessment.maturity_score:
            raise ValueError("explanation maturity score must match assessment")
        if explanation.metadata.get("assessment_id") != assessment.assessment_id:
            raise ValueError("explanation assessment identity must match")
        if explanation.metadata.get("candidate_id") != assessment.candidate_id:
            raise ValueError("explanation candidate identity must match")

    @staticmethod
    def _fresh_factor_strength(
        available_factors: Tuple[str, ...],
        factor_values: TypingMapping[str, Any],
    ) -> float:
        if not available_factors:
            return 0.0
        weight_total = sum(
            EMERGENCE_FACTOR_WEIGHTS[factor_name]
            for factor_name in available_factors
        )
        weighted = sum(
            factor_values[factor_name].score
            * EMERGENCE_FACTOR_WEIGHTS[factor_name]
            for factor_name in available_factors
        )
        return round(weighted / weight_total, 6)

    @staticmethod
    def _independence_proxy(active_count: int) -> float:
        if active_count <= 0:
            return 0.0
        return float(min(active_count, 4) * 25)

    @staticmethod
    def _early_structure_proxy(
        build_result: EarlyBirdCandidateBuildResult,
    ) -> float:
        structure = build_result.factor_values["structure_event"]
        if structure.availability is not FactorAvailability.AVAILABLE:
            return 50.0
        score = structure.score
        if score <= 20.0:
            return round(70.0 + score / 20.0 * 30.0, 6)
        if score <= 60.0:
            return round(100.0 - (score - 20.0), 6)
        return round(max(0.0, 60.0 - (score - 60.0) * 1.5), 6)

    @staticmethod
    def _incomplete_confirmation_proxy(
        build_result: EarlyBirdCandidateBuildResult,
    ) -> float:
        values = build_result.factor_values
        has_initiating = any(
            values[factor_name].availability is FactorAvailability.AVAILABLE
            and values[factor_name].score >= ACTIVE_FACTOR_THRESHOLD
            for factor_name in INITIATING_FACTORS
        )
        if not has_initiating:
            return 0.0
        measured_gaps = tuple(
            (CONFIRMATION_THRESHOLD - values[factor_name].score)
            / CONFIRMATION_THRESHOLD
            * 100.0
            for factor_name in CONFIRMATION_FACTORS
            if values[factor_name].availability is FactorAvailability.AVAILABLE
            and values[factor_name].score < CONFIRMATION_THRESHOLD
        )
        if not measured_gaps:
            return 0.0
        return round(sum(measured_gaps) / len(measured_gaps), 6)

    @staticmethod
    def _independent_factor_counts(
        build_result: EarlyBirdCandidateBuildResult,
    ) -> Tuple[int, int]:
        values = build_result.factor_values
        supported = tuple(
            factor_name
            for factor_name in CANONICAL_FACTOR_NAMES
            if values[factor_name].availability
            is not FactorAvailability.UNSUPPORTED
        )
        active = sum(
            values[factor_name].availability is FactorAvailability.AVAILABLE
            and values[factor_name].score >= ACTIVE_FACTOR_THRESHOLD
            for factor_name in supported
        )
        return active, len(supported)

    @staticmethod
    def _development_stage(
        *,
        emergence: float,
        horizon: float,
        maturity: float,
        detection_confidence: float,
        has_emergence_factors: bool,
        warnings: Tuple[str, ...],
    ) -> EmergingStage:
        if (
            not has_emergence_factors
            or detection_confidence < UNKNOWN_DETECTION_CONFIDENCE
        ):
            return EmergingStage.UNKNOWN
        over_mature_warning = any(
            "over-mature" in warning.lower() for warning in warnings
        )
        if (
            (maturity >= 85.0 and horizon < 25.0)
            or (over_mature_warning and horizon < 30.0)
        ):
            return EmergingStage.EXHAUSTED
        if maturity >= 70.0 and horizon < 45.0:
            return EmergingStage.MATURE
        if emergence >= 35.0 and horizon >= 60.0 and maturity < 45.0:
            return EmergingStage.EMERGING
        if (
            emergence >= 45.0
            and 35.0 <= horizon < 60.0
            and 35.0 <= maturity < 70.0
        ):
            return EmergingStage.BUILDING
        if emergence < 35.0 and horizon >= 65.0 and maturity < 35.0:
            return EmergingStage.SEED
        return EmergingStage.UNKNOWN

    @staticmethod
    def _supporting_factors(
        build_result: EarlyBirdCandidateBuildResult,
        explanation: EarlyBirdExplanation,
    ) -> Tuple[str, ...]:
        values = build_result.factor_values
        measured = tuple(
            factor_name
            for factor_name in CANONICAL_FACTOR_NAMES
            if values[factor_name].availability is FactorAvailability.AVAILABLE
            and values[factor_name].score >= ACTIVE_FACTOR_THRESHOLD
        )
        return tuple(sorted(
            measured,
            key=lambda factor_name: (
                -explanation.factor_breakdown[factor_name][
                    "weighted_contribution"
                ],
                CANONICAL_FACTOR_NAMES.index(factor_name),
            ),
        ))

    @staticmethod
    def _limiting_factors(
        assessment: EarlyBirdAssessment,
        build_result: EarlyBirdCandidateBuildResult,
        active_emergence: Tuple[str, ...],
    ) -> Tuple[str, ...]:
        values = build_result.factor_values
        limitations = []
        momentum = values["momentum_shift"]
        if (
            momentum.availability is FactorAvailability.AVAILABLE
            and momentum.score < ACTIVE_FACTOR_THRESHOLD
        ):
            limitations.append("Measured momentum remains weak.")
        volume = values["volume_expansion"]
        if (
            volume.availability is FactorAvailability.AVAILABLE
            and volume.score < ACTIVE_FACTOR_THRESHOLD
        ):
            limitations.append("Measured volume expansion remains weak.")
        if assessment.maturity_score >= 70.0:
            limitations.append("Measured maturity is already high.")
        for factor_name in build_result.stale_factors:
            limitations.append("{0} is stale.".format(_label(factor_name)))
        if (
            build_result.candidate.data_completeness_score
            < LOW_COMPLETENESS_THRESHOLD
        ):
            limitations.append("Supported factor completeness is low.")
        if build_result.candidate.quality < LOW_QUALITY_THRESHOLD:
            limitations.append("Available factor quality is low.")
        if len(active_emergence) == 1:
            limitations.append("Emergence evidence is concentrated in one factor.")
        for factor_name in INITIATING_FACTORS:
            value = values[factor_name]
            if value.availability is not FactorAvailability.AVAILABLE:
                limitations.append(
                    "{0} is unavailable ({1}).".format(
                        _label(factor_name),
                        value.availability.value,
                    )
                )
        return _deduplicate(limitations)

    @staticmethod
    def _reasons(
        assessment: EarlyBirdAssessment,
        build_result: EarlyBirdCandidateBuildResult,
        supporting: Tuple[str, ...],
        active_emergence: Tuple[str, ...],
    ) -> Tuple[str, ...]:
        reasons = []
        active_set = set(active_emergence)
        if "structure_event" in active_set and "volume_expansion" in active_set:
            reasons.append(
                "Measured structure activity and volume expansion describe a developing market situation."
            )
        if assessment.maturity_score < 35.0:
            reasons.append(
                "The situation remains early because measured maturity is low."
            )
        if "funding_divergence" in active_set:
            reasons.append(
                "Funding divergence contributes to emergence without determining direction."
            )
        if len(supporting) >= 3:
            reasons.append(
                "Several independent measured factors support the emergence classification."
            )
        if not reasons:
            reasons.append(
                "The stage reflects the currently available measured evidence and maturity."
            )
        return _deduplicate(reasons)

    @staticmethod
    def _warnings(
        assessment: EarlyBirdAssessment,
        build_result: EarlyBirdCandidateBuildResult,
        explanation: EarlyBirdExplanation,
        *,
        confidence: float,
        horizon: float,
        available_emergence: Tuple[str, ...],
        active_emergence: Tuple[str, ...],
    ) -> Tuple[str, ...]:
        warnings = list(explanation.warnings)
        if confidence < LOW_DETECTION_CONFIDENCE:
            warnings.append(
                "Detection confidence is limited by completeness, quality, independence, or freshness."
            )
        if not available_emergence:
            warnings.append("No measured emergence factor is available.")
        if len(active_emergence) == 1:
            warnings.append("Emergence evidence is concentrated in one factor.")
        if assessment.maturity_score >= 70.0 and horizon < 30.0:
            warnings.append("High measured maturity leaves limited horizon.")
        unavailable_initiating = tuple(
            factor_name
            for factor_name in INITIATING_FACTORS
            if build_result.factor_values[factor_name].availability
            is not FactorAvailability.AVAILABLE
        )
        if unavailable_initiating:
            warnings.append(
                "Initiating evidence is unavailable for: {0}.".format(
                    ", ".join(_label(name) for name in unavailable_initiating)
                )
            )
        if build_result.stale_factors:
            warnings.append("Stale evidence is excluded from emergence strength.")
        if (
            build_result.candidate.data_completeness_score
            < LOW_COMPLETENESS_THRESHOLD
        ):
            warnings.append("Supported factor data is incomplete.")
        return _deduplicate(warnings)


def format_emerging_situation(situation: EmergingSituation) -> str:
    """Render one emerging situation as plain descriptive terminal text."""

    if not isinstance(situation, EmergingSituation):
        raise TypeError("situation must be an EmergingSituation")
    lines = [
        situation.asset,
        "",
        "Emergence: {0:.2f}".format(situation.emergence_score),
        "Horizon: {0:.2f}".format(situation.horizon_score),
        "Stage: {0}".format(situation.stage.value),
        "Detection confidence: {0:.2f}".format(
            situation.detection_confidence
        ),
        "",
        "Supporting factors:",
    ]
    lines.extend(
        "- {0}".format(_label(factor_name))
        for factor_name in situation.supporting_factors
    )
    if not situation.supporting_factors:
        lines.append("- none")
    lines.extend(("", "Limiting factors:"))
    lines.extend(
        "- {0}".format(item) for item in situation.limiting_factors
    )
    if not situation.limiting_factors:
        lines.append("- none")
    lines.extend(("", "Missing factors:"))
    lines.extend(
        "- {0}".format(_label(factor_name))
        for factor_name in situation.missing_factors
    )
    if not situation.missing_factors:
        lines.append("- none")
    lines.extend(("", "Why:"))
    lines.extend("- {0}".format(reason) for reason in situation.reasons)
    if situation.warnings:
        lines.extend(("", "Warnings:"))
        lines.extend("- {0}".format(warning) for warning in situation.warnings)
    return "\n".join(lines)


__all__ = [
    "EmergingSituation",
    "EmergingSituationEngine",
    "EmergingStage",
    "format_emerging_situation",
]
