"""Descriptive explainability for Early Bird assessments and rankings."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from numbers import Real
from types import MappingProxyType
from typing import Any, Dict, Iterable, Mapping as TypingMapping, Optional, Tuple

from app.intelligence.early_bird.builder import (
    CANONICAL_FACTOR_NAMES,
    EarlyBirdCandidateBuildResult,
)
from app.intelligence.early_bird.models import (
    EarlyBirdAssessment,
    _frozen_mapping,
    _mapping_payload,
    _percentage,
    _required_text,
    _string_tuple,
    _to_plain,
)


EXPLANATION_VERSION = 1
MATERIAL_FACTOR_THRESHOLD = 35.0

FACTOR_LABELS = MappingProxyType({
    "whale_activity": "Whale Activity",
    "open_interest_change": "Open Interest Change",
    "funding_divergence": "Funding Divergence",
    "volume_expansion": "Volume Expansion",
    "relative_strength": "Relative Strength",
    "liquidity_event": "Liquidity Event",
    "structure_event": "Structure Event",
    "momentum_shift": "Momentum Shift",
})


def _fraction(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{0} must be a real number".format(field_name))
    normalized = float(value)
    if not 0.0 <= normalized <= 1.0:
        raise ValueError("{0} must be between 0 and 1".format(field_name))
    return normalized


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


def _normalized_percentages(
    contributions: TypingMapping[str, float],
) -> Dict[str, float]:
    total = sum(contributions.values())
    if total <= 0.0:
        return {factor_name: 0.0 for factor_name in contributions}

    percentages = {}
    running_total = 0.0
    factor_names = tuple(contributions)
    for factor_name in factor_names[:-1]:
        percentage = round(contributions[factor_name] / total * 100.0, 6)
        percentages[factor_name] = percentage
        running_total += percentage
    percentages[factor_names[-1]] = round(100.0 - running_total, 6)
    return percentages


@dataclass(frozen=True)
class EarlyBirdExplanation:
    """Immutable descriptive explanation of one ranked Early Bird result."""

    asset: str
    opportunity_score: float
    priority_score: float
    maturity_score: float
    factor_breakdown: TypingMapping[str, Any]
    top_positive_factors: Tuple[str, ...]
    missing_factors: Tuple[str, ...]
    unsupported_factors: Tuple[str, ...]
    error_factors: Tuple[str, ...]
    warnings: Tuple[str, ...]
    why_ranked_here: Tuple[str, ...]
    why_not_higher: Tuple[str, ...]
    metadata: TypingMapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "asset",
            _required_text(self.asset, "asset").upper(),
        )
        for field_name in (
            "opportunity_score",
            "priority_score",
            "maturity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _percentage(getattr(self, field_name), field_name),
            )

        if not isinstance(self.factor_breakdown, Mapping):
            raise TypeError("factor_breakdown must be a mapping")
        normalized_breakdown = {}
        for factor_name, raw_item in self.factor_breakdown.items():
            normalized_name = _required_text(factor_name, "factor name")
            if not isinstance(raw_item, Mapping):
                raise TypeError("factor breakdown entries must be mappings")
            item = dict(raw_item)
            if set(item) != {
                "raw_score",
                "weight",
                "weighted_contribution",
                "contribution_percent",
            }:
                raise ValueError("factor breakdown entry fields are invalid")
            normalized_breakdown[normalized_name] = {
                "raw_score": _percentage(item["raw_score"], "raw_score"),
                "weight": _fraction(item["weight"], "weight"),
                "weighted_contribution": _percentage(
                    item["weighted_contribution"],
                    "weighted_contribution",
                ),
                "contribution_percent": _percentage(
                    item["contribution_percent"],
                    "contribution_percent",
                ),
            }
        if not normalized_breakdown:
            raise ValueError("factor_breakdown must contain measured factors")
        weighted_total = sum(
            item["weighted_contribution"]
            for item in normalized_breakdown.values()
        )
        percentage_total = sum(
            item["contribution_percent"]
            for item in normalized_breakdown.values()
        )
        if weighted_total > 0.0 and abs(percentage_total - 100.0) > 0.0001:
            raise ValueError(
                "positive contribution percentages must sum to 100"
            )
        if weighted_total == 0.0 and abs(percentage_total) > 0.0001:
            raise ValueError(
                "zero weighted contribution requires zero percentages"
            )

        collection_fields = (
            "top_positive_factors",
            "missing_factors",
            "unsupported_factors",
            "error_factors",
            "warnings",
            "why_ranked_here",
            "why_not_higher",
        )
        for field_name in collection_fields:
            object.__setattr__(
                self,
                field_name,
                _string_tuple(getattr(self, field_name), field_name),
            )
        if not set(self.top_positive_factors).issubset(normalized_breakdown):
            raise ValueError("top_positive_factors must be measured factors")
        if not self.why_ranked_here:
            raise ValueError("why_ranked_here must not be empty")
        if not self.why_not_higher:
            raise ValueError("why_not_higher must not be empty")

        non_available = (
            set(self.missing_factors)
            | set(self.unsupported_factors)
            | set(self.error_factors)
        )
        non_available_count = (
            len(self.missing_factors)
            + len(self.unsupported_factors)
            + len(self.error_factors)
        )
        if len(non_available) != non_available_count:
            raise ValueError("factor availability groups must not overlap")
        if set(normalized_breakdown) & non_available:
            raise ValueError("non-AVAILABLE factors cannot appear in breakdown")

        object.__setattr__(
            self,
            "factor_breakdown",
            _frozen_mapping(normalized_breakdown, "factor_breakdown"),
        )
        object.__setattr__(
            self,
            "metadata",
            _frozen_mapping(self.metadata, "metadata"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "opportunity_score": self.opportunity_score,
            "priority_score": self.priority_score,
            "maturity_score": self.maturity_score,
            "factor_breakdown": _to_plain(self.factor_breakdown),
            "top_positive_factors": list(self.top_positive_factors),
            "missing_factors": list(self.missing_factors),
            "unsupported_factors": list(self.unsupported_factors),
            "error_factors": list(self.error_factors),
            "warnings": list(self.warnings),
            "why_ranked_here": list(self.why_ranked_here),
            "why_not_higher": list(self.why_not_higher),
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(
        cls,
        data: TypingMapping[str, Any],
    ) -> "EarlyBirdExplanation":
        return cls(**_mapping_payload(data, "early bird explanation"))


class EarlyBirdExplainer:
    """Build explanations without recalculating or changing any score."""

    def explain(
        self,
        assessment: EarlyBirdAssessment,
        build_result: EarlyBirdCandidateBuildResult,
        *,
        previous_assessment: Optional[EarlyBirdAssessment] = None,
        previous_build_result: Optional[EarlyBirdCandidateBuildResult] = None,
    ) -> EarlyBirdExplanation:
        self._validate_pair(assessment, build_result, "current")
        previous = self._previous_pair(
            assessment,
            previous_assessment,
            previous_build_result,
        )

        breakdown, ordered_positive = self._breakdown(assessment, build_result)
        why_ranked = self._why_ranked(breakdown, ordered_positive)
        why_not = self._why_not_higher(
            assessment,
            build_result,
            breakdown,
            previous,
        )
        warnings = self._warnings(assessment, build_result)
        contribution_total = round(
            sum(
                item["contribution_percent"]
                for item in breakdown.values()
            ),
            6,
        )
        weighted_total = round(
            sum(
                item["weighted_contribution"]
                for item in breakdown.values()
            ),
            6,
        )
        return EarlyBirdExplanation(
            asset=assessment.asset,
            opportunity_score=assessment.opportunity_score,
            priority_score=assessment.priority_score,
            maturity_score=assessment.maturity_score,
            factor_breakdown=breakdown,
            top_positive_factors=ordered_positive,
            missing_factors=build_result.missing_factors,
            unsupported_factors=build_result.unsupported_factors,
            error_factors=build_result.error_factors,
            warnings=warnings,
            why_ranked_here=why_ranked,
            why_not_higher=why_not,
            metadata={
                "explanation_version": EXPLANATION_VERSION,
                "assessment_id": assessment.assessment_id,
                "candidate_id": assessment.candidate_id,
                "rank": assessment.rank,
                "previous_asset": (
                    previous[0].asset if previous is not None else None
                ),
                "previous_rank": (
                    previous[0].rank if previous is not None else None
                ),
                "available_weighted_contribution": weighted_total,
                "contribution_percent_total": contribution_total,
                "zero_contribution_basis": weighted_total == 0.0,
                "stale_factors": list(build_result.stale_factors),
            },
        )

    def explain_ranked(
        self,
        entries: Iterable[
            Tuple[EarlyBirdAssessment, EarlyBirdCandidateBuildResult]
        ],
    ) -> Tuple[EarlyBirdExplanation, ...]:
        if isinstance(entries, (str, bytes)):
            raise TypeError("entries must be an iterable of assessment pairs")
        try:
            values = tuple(entries)
        except TypeError as exc:
            raise TypeError(
                "entries must be an iterable of assessment pairs"
            ) from exc
        normalized = []
        for entry in values:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise TypeError("each entry must be an assessment/build-result pair")
            assessment, build_result = entry
            self._validate_pair(assessment, build_result, "ranked")
            if assessment.rank is None:
                raise ValueError("ranked assessments must have a rank")
            normalized.append((assessment, build_result))
        normalized.sort(key=lambda item: item[0].rank)
        ranks = tuple(item[0].rank for item in normalized)
        if ranks and ranks != tuple(range(ranks[0], ranks[0] + len(ranks))):
            raise ValueError("ranked entries must have contiguous ranks")

        explanations = []
        for index, (assessment, build_result) in enumerate(normalized):
            previous_assessment = None
            previous_build_result = None
            if index > 0:
                previous_assessment, previous_build_result = normalized[index - 1]
            explanations.append(
                self.explain(
                    assessment,
                    build_result,
                    previous_assessment=previous_assessment,
                    previous_build_result=previous_build_result,
                )
            )
        return tuple(explanations)

    @staticmethod
    def _validate_pair(
        assessment: Any,
        build_result: Any,
        label: str,
    ) -> None:
        if not isinstance(assessment, EarlyBirdAssessment):
            raise TypeError("{0} assessment is invalid".format(label))
        if not isinstance(build_result, EarlyBirdCandidateBuildResult):
            raise TypeError("{0} build result is invalid".format(label))
        if assessment.candidate_id != build_result.candidate.candidate_id:
            raise ValueError("assessment and build result candidate IDs must match")
        if assessment.asset != build_result.candidate.asset:
            raise ValueError("assessment and build result assets must match")

    def _previous_pair(
        self,
        assessment: EarlyBirdAssessment,
        previous_assessment: Optional[EarlyBirdAssessment],
        previous_build_result: Optional[EarlyBirdCandidateBuildResult],
    ) -> Optional[Tuple[EarlyBirdAssessment, EarlyBirdCandidateBuildResult]]:
        if previous_assessment is None and previous_build_result is None:
            return None
        if previous_assessment is None or previous_build_result is None:
            raise ValueError("previous assessment and build result are both required")
        self._validate_pair(previous_assessment, previous_build_result, "previous")
        if assessment.rank is None or previous_assessment.rank is None:
            raise ValueError("comparison requires ranked assessments")
        if previous_assessment.rank != assessment.rank - 1:
            raise ValueError("comparison must use the immediately higher rank")
        return previous_assessment, previous_build_result

    @staticmethod
    def _breakdown(
        assessment: EarlyBirdAssessment,
        build_result: EarlyBirdCandidateBuildResult,
    ) -> Tuple[Dict[str, Dict[str, float]], Tuple[str, ...]]:
        raw_contributions = assessment.factor_contributions
        measured = {}
        for factor_name in CANONICAL_FACTOR_NAMES:
            if factor_name not in build_result.available_factors:
                continue
            raw_item = raw_contributions.get(factor_name)
            if not isinstance(raw_item, Mapping):
                raise ValueError(
                    "assessment contribution is missing for {0}".format(factor_name)
                )
            raw_score = float(raw_item["score"])
            weight = float(raw_item["weight"])
            weighted = float(raw_item["weighted_contribution"])
            measured[factor_name] = {
                "raw_score": raw_score,
                "weight": weight,
                "weighted_contribution": weighted,
            }

        percentages = _normalized_percentages({
            factor_name: item["weighted_contribution"]
            for factor_name, item in measured.items()
        })
        breakdown = {
            factor_name: dict(
                item,
                contribution_percent=percentages[factor_name],
            )
            for factor_name, item in measured.items()
        }
        ordered_positive = tuple(
            factor_name
            for factor_name, item in sorted(
                measured.items(),
                key=lambda pair: (
                    -pair[1]["weighted_contribution"],
                    CANONICAL_FACTOR_NAMES.index(pair[0]),
                ),
            )
            if item["weighted_contribution"] > 0.0
        )
        return breakdown, ordered_positive

    @staticmethod
    def _why_ranked(
        breakdown: TypingMapping[str, TypingMapping[str, float]],
        ordered_positive: Tuple[str, ...],
    ) -> Tuple[str, ...]:
        reasons = []
        if ordered_positive:
            leading = ordered_positive[0]
            reasons.append(
                "Highest measured contributor is {0} ({1:.2f} weighted points)."
                .format(
                    _label(leading),
                    breakdown[leading]["weighted_contribution"],
                )
            )
        else:
            reasons.append("No measured factor supplied a positive contribution.")

        funding = breakdown.get("funding_divergence")
        if funding is not None and funding["contribution_percent"] >= 10.0:
            reasons.append(
                "Funding Divergence supplies {0:.2f}% of measured opportunity evidence."
                .format(funding["contribution_percent"])
            )
        structure = breakdown.get("structure_event")
        if structure is not None and structure["raw_score"] < MATERIAL_FACTOR_THRESHOLD:
            reasons.append(
                "Structure activity remains early at raw score {0:.2f}."
                .format(structure["raw_score"])
            )
        momentum = breakdown.get("momentum_shift")
        if momentum is not None and 0.0 < momentum["raw_score"] < MATERIAL_FACTOR_THRESHOLD:
            reasons.append(
                "Momentum is developing but remains below the material threshold."
            )
        return _deduplicate(reasons)

    def _why_not_higher(
        self,
        assessment: EarlyBirdAssessment,
        build_result: EarlyBirdCandidateBuildResult,
        breakdown: TypingMapping[str, TypingMapping[str, float]],
        previous: Optional[
            Tuple[EarlyBirdAssessment, EarlyBirdCandidateBuildResult]
        ],
    ) -> Tuple[str, ...]:
        limitations = []
        for factor_name in build_result.missing_factors:
            limitations.append(
                "{0} is missing and cannot support a higher score."
                .format(_label(factor_name))
            )
        for factor_name in build_result.stale_factors:
            limitations.append(
                "{0} is stale and is excluded from measured contributions."
                .format(_label(factor_name))
            )
        for factor_name in build_result.unsupported_factors:
            limitations.append(
                "{0} is unsupported and cannot support this ranking."
                .format(_label(factor_name))
            )
        for factor_name in build_result.error_factors:
            limitations.append(
                "{0} is in error and is excluded from measured contributions."
                .format(_label(factor_name))
            )

        completeness = build_result.candidate.data_completeness_score
        if completeness < 100.0:
            limitations.append(
                "Data completeness is {0:.2f}%, limiting reliability-adjusted opportunity."
                .format(completeness)
            )
        structure = breakdown.get("structure_event")
        if structure is not None and structure["raw_score"] < MATERIAL_FACTOR_THRESHOLD:
            limitations.append("Measured structure evidence is still immature.")
        momentum = breakdown.get("momentum_shift")
        if momentum is not None and momentum["raw_score"] < MATERIAL_FACTOR_THRESHOLD:
            limitations.append("Measured momentum contribution remains weak.")

        if previous is not None:
            previous_assessment, previous_build_result = previous
            previous_breakdown, _ = self._breakdown(
                previous_assessment,
                previous_build_result,
            )
            common_factors = tuple(
                factor_name
                for factor_name in CANONICAL_FACTOR_NAMES
                if factor_name in breakdown and factor_name in previous_breakdown
            )
            deficits = []
            for factor_name in common_factors:
                difference = (
                    previous_breakdown[factor_name]["weighted_contribution"]
                    - breakdown[factor_name]["weighted_contribution"]
                )
                if difference > 0.0:
                    deficits.append((factor_name, difference))
            deficits.sort(
                key=lambda item: (-item[1], CANONICAL_FACTOR_NAMES.index(item[0]))
            )
            for factor_name, difference in deficits:
                limitations.append(
                    "Compared with {0} above, {1} contributed {2:.2f} fewer weighted points."
                    .format(
                        previous_assessment.asset,
                        _label(factor_name),
                        difference,
                    )
                )
            if not deficits:
                limitations.append(
                    "Shared measured factor contributions do not explain the gap to {0}; "
                    "freshness, urgency, quality, or deterministic tie-breaking may account for it."
                    .format(previous_assessment.asset)
                )
        elif assessment.rank == 1:
            limitations.append("This is the highest-ranked asset in the supplied set.")
        elif assessment.rank is not None:
            limitations.append("No immediately higher ranked comparison was supplied.")

        if not limitations:
            limitations.append("No explicit measured limitation was identified.")
        return _deduplicate(limitations)

    @staticmethod
    def _warnings(
        assessment: EarlyBirdAssessment,
        build_result: EarlyBirdCandidateBuildResult,
    ) -> Tuple[str, ...]:
        assessment_warnings = tuple(assessment.warnings)
        if "whale_activity" not in build_result.available_factors:
            assessment_warnings = tuple(
                warning
                for warning in assessment_warnings
                if warning
                != "No whale activity is present in this whale-first assessment."
            )
        return _deduplicate(tuple(build_result.warnings) + assessment_warnings)


def format_explanation(explanation: EarlyBirdExplanation) -> str:
    """Render one explanation as plain terminal text."""

    if not isinstance(explanation, EarlyBirdExplanation):
        raise TypeError("explanation must be an EarlyBirdExplanation")
    lines = [
        explanation.asset,
        "Opportunity: {0:.2f}".format(explanation.opportunity_score),
        "Priority: {0:.2f}".format(explanation.priority_score),
        "Maturity: {0:.2f}".format(explanation.maturity_score),
        "",
        "Contribution:",
    ]
    ordered = tuple(explanation.top_positive_factors) + tuple(
        factor_name
        for factor_name in explanation.factor_breakdown
        if factor_name not in explanation.top_positive_factors
    )
    for factor_name in ordered:
        item = explanation.factor_breakdown[factor_name]
        lines.append(
            "- {0}: {1:.2f}% (raw {2:.2f}, weight {3:.2f}, weighted {4:.2f})"
            .format(
                _label(factor_name),
                item["contribution_percent"],
                item["raw_score"],
                item["weight"],
                item["weighted_contribution"],
            )
        )

    sections = (
        ("Missing", explanation.missing_factors),
        ("Unsupported", explanation.unsupported_factors),
        ("Errors", explanation.error_factors),
    )
    for heading, factors in sections:
        lines.extend(("", "{0}:".format(heading)))
        lines.extend(
            "- {0}".format(_label(factor_name)) for factor_name in factors
        )
        if not factors:
            lines.append("- none")

    lines.extend(("", "Why ranked here:"))
    lines.extend("- {0}".format(reason) for reason in explanation.why_ranked_here)
    lines.extend(("", "Why not higher:"))
    lines.extend("- {0}".format(reason) for reason in explanation.why_not_higher)
    if explanation.warnings:
        lines.extend(("", "Warnings:"))
        lines.extend("- {0}".format(warning) for warning in explanation.warnings)
    return "\n".join(lines)


def format_explanations(
    explanations: Iterable[EarlyBirdExplanation],
) -> str:
    """Render multiple explanations in supplied rank order."""

    if isinstance(explanations, (str, bytes)):
        raise TypeError("explanations must be an iterable")
    try:
        values = tuple(explanations)
    except TypeError as exc:
        raise TypeError("explanations must be an iterable") from exc
    if not all(isinstance(item, EarlyBirdExplanation) for item in values):
        raise TypeError("explanations must contain EarlyBirdExplanation objects")
    return "\n\n".join(format_explanation(item) for item in values)


__all__ = [
    "EarlyBirdExplainer",
    "EarlyBirdExplanation",
    "format_explanation",
    "format_explanations",
]
