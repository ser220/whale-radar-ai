"""Pure mapping from ranked Early Bird artifacts to Timeline version 1."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterable, Mapping as TypingMapping, Optional, Tuple

from app.intelligence.early_bird import (
    EarlyBirdExplainer,
    EarlyBirdExplanation,
    EmergingSituation,
    EmergingSituationEngine,
    EmergingStage,
    FactorAvailability,
)
from app.intelligence.timeline.models import (
    MarketSituationTimeline,
    MarketSituationTimelineEntry,
    SituationDNA,
    _frozen_mapping,
    _mapping_payload,
    _parse_datetime,
    _required_text,
    _to_plain,
    _utc_datetime,
)


FACTOR_NAMES = (
    "whale_activity",
    "funding_divergence",
    "volume_expansion",
    "structure_event",
    "momentum_shift",
    "relative_strength",
    "open_interest_change",
    "liquidity_event",
)

FACTOR_LABELS = MappingProxyType({
    "whale_activity": "Whale Activity",
    "funding_divergence": "Funding Divergence",
    "volume_expansion": "Volume Expansion",
    "structure_event": "Structure Event",
    "momentum_shift": "Momentum Shift",
    "relative_strength": "Relative Strength",
    "open_interest_change": "Open Interest Change",
    "liquidity_event": "Liquidity Event",
})

ADAPTER_VERSION = 1


def _attributes(value: Any, names: Iterable[str], label: str) -> None:
    missing = tuple(name for name in names if not hasattr(value, name))
    if missing:
        raise TypeError(
            "{0} is missing required attributes: {1}".format(
                label,
                ", ".join(missing),
            )
        )


def _error_text(exc: Exception) -> str:
    message = str(exc).strip() or "No error detail was provided."
    return "{0}: {1}".format(type(exc).__name__, message)


def _safe_identity_part(value: Any, field_name: str) -> str:
    normalized = _required_text(value, field_name).lower()
    parts = []
    current = []
    for character in normalized:
        if character.isalnum() and character.isascii():
            current.append(character)
        elif current:
            parts.append("".join(current))
            current = []
    if current:
        parts.append("".join(current))
    safe = "-".join(parts)
    if not safe:
        raise ValueError("{0} has no usable identity characters".format(field_name))
    return safe


def deterministic_run_local_ids(scan_item: Any) -> Tuple[str, str]:
    """Build deterministic process-local IDs, not a permanent identity policy."""

    _attributes(
        scan_item,
        ("symbol", "assessment", "scanned_at"),
        "scan_item",
    )
    _attributes(scan_item.assessment, ("candidate_id",), "assessment")
    asset = _safe_identity_part(scan_item.symbol, "asset")
    candidate = _safe_identity_part(
        scan_item.assessment.candidate_id,
        "candidate_id",
    )
    scanned_at = _utc_datetime(scan_item.scanned_at, "scanned_at")
    timestamp = scanned_at.strftime("%Y%m%dT%H%M%S%fZ")
    timeline_id = "run-local:{0}:{1}:{2}".format(asset, timestamp, candidate)
    return timeline_id, "{0}:initial".format(timeline_id)


@dataclass(frozen=True)
class EarlyBirdTimelineResult:
    """One immutable Timeline v1 plus its source interpretation artifacts."""

    timeline: MarketSituationTimeline
    explanation: EarlyBirdExplanation
    emerging_situation: EmergingSituation
    source_assessment_id: str
    source_candidate_id: str
    created_at: datetime
    metadata: TypingMapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.timeline, MarketSituationTimeline):
            raise TypeError("timeline must be a MarketSituationTimeline")
        if not isinstance(self.explanation, EarlyBirdExplanation):
            raise TypeError("explanation must be an EarlyBirdExplanation")
        if not isinstance(self.emerging_situation, EmergingSituation):
            raise TypeError("emerging_situation must be an EmergingSituation")
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
            "created_at",
            _utc_datetime(self.created_at, "created_at"),
        )
        if self.timeline.asset != self.explanation.asset:
            raise ValueError("timeline and explanation assets must match")
        if self.timeline.asset != self.emerging_situation.asset:
            raise ValueError("timeline and emerging situation assets must match")
        if self.timeline.version != 1 or len(self.timeline.entries) != 1:
            raise ValueError("result timeline must contain exactly one version 1 entry")
        if self.created_at != self.timeline.created_at:
            raise ValueError("result and timeline created_at must match")
        entry = self.timeline.entries[0]
        if entry.created_at != self.created_at:
            raise ValueError("result and timeline entry created_at must match")
        if self.source_assessment_id != self.emerging_situation.source_assessment_id:
            raise ValueError("source assessment identity must match")
        if self.source_candidate_id != self.emerging_situation.source_candidate_id:
            raise ValueError("source candidate identity must match")
        if entry.source_assessment_id != self.source_assessment_id:
            raise ValueError("timeline entry assessment identity must match")
        if entry.source_candidate_id != self.source_candidate_id:
            raise ValueError("timeline entry candidate identity must match")
        object.__setattr__(
            self,
            "metadata",
            _frozen_mapping(self.metadata, "metadata"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timeline": self.timeline.to_dict(),
            "explanation": self.explanation.to_dict(),
            "emerging_situation": self.emerging_situation.to_dict(),
            "source_assessment_id": self.source_assessment_id,
            "source_candidate_id": self.source_candidate_id,
            "created_at": self.created_at.isoformat(),
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: TypingMapping[str, Any]) -> "EarlyBirdTimelineResult":
        payload = _mapping_payload(data, "early bird timeline result")
        payload["timeline"] = MarketSituationTimeline.from_dict(payload.get("timeline"))
        payload["explanation"] = EarlyBirdExplanation.from_dict(
            payload.get("explanation")
        )
        payload["emerging_situation"] = EmergingSituation.from_dict(
            payload.get("emerging_situation")
        )
        payload["created_at"] = _parse_datetime(
            payload.get("created_at"),
            "created_at",
        )
        return cls(**payload)


@dataclass(frozen=True)
class EarlyBirdTimelineBatchResult:
    """Process-local successes and isolated construction failures."""

    results: Tuple[EarlyBirdTimelineResult, ...]
    errors: TypingMapping[str, str]
    stage_distribution: TypingMapping[str, int]
    top_assets: Tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.results, (str, bytes, set, frozenset)):
            raise TypeError("results must be an ordered collection")
        try:
            results = tuple(self.results)
        except TypeError as exc:
            raise TypeError("results must be an ordered collection") from exc
        if not all(isinstance(item, EarlyBirdTimelineResult) for item in results):
            raise TypeError("results must contain EarlyBirdTimelineResult objects")
        if not isinstance(self.errors, Mapping):
            raise TypeError("errors must be a mapping")
        errors = {
            _required_text(asset, "error asset").upper(): _required_text(
                message,
                "error message",
            )
            for asset, message in self.errors.items()
        }
        if not isinstance(self.stage_distribution, Mapping):
            raise TypeError("stage_distribution must be a mapping")
        distribution = {}
        for stage, count in self.stage_distribution.items():
            normalized_stage = EmergingStage(stage).value
            if isinstance(count, bool) or not isinstance(count, int) or count < 1:
                raise ValueError("stage distribution counts must be positive integers")
            distribution[normalized_stage] = count
        expected_assets = tuple(result.timeline.asset for result in results)
        top_assets = tuple(
            _required_text(asset, "top asset").upper() for asset in self.top_assets
        )
        if top_assets != expected_assets:
            raise ValueError("top_assets must match successful result order")
        expected_distribution = {}
        for stage in EmergingStage:
            count = sum(
                result.timeline.current_stage is stage for result in results
            )
            if count:
                expected_distribution[stage.value] = count
        if distribution != expected_distribution:
            raise ValueError("stage_distribution must match successful results")
        object.__setattr__(self, "results", results)
        object.__setattr__(self, "errors", MappingProxyType(errors))
        object.__setattr__(
            self,
            "stage_distribution",
            MappingProxyType(expected_distribution),
        )
        object.__setattr__(self, "top_assets", top_assets)


class EarlyBirdTimelineAdapter:
    """Map real normalized Early Bird artifacts into a Timeline v1."""

    def create_timeline(
        self,
        *,
        scan_item: Any,
        explanation: EarlyBirdExplanation,
        emerging_situation: EmergingSituation,
        timeline_id: str,
        entry_id: str,
        timestamp: Optional[datetime] = None
    ) -> EarlyBirdTimelineResult:
        assessment, build_result, candidate = self._validate_inputs(
            scan_item,
            explanation,
            emerging_situation,
        )
        created_at = (
            emerging_situation.evaluated_at
            if timestamp is None
            else _utc_datetime(timestamp, "timestamp")
        )
        normalized_timeline_id = _required_text(timeline_id, "timeline_id")
        normalized_entry_id = _required_text(entry_id, "entry_id")
        dna = self._situation_dna(
            scan_item,
            explanation,
            emerging_situation,
        )
        observed_events = tuple(
            ["fast_event:{0}".format(value) for value in candidate.fast_event_ids]
            + [
                "observation:{0}".format(value)
                for value in candidate.observation_ids
            ]
            + [
                "measured_factor:{0}".format(factor_name)
                for factor_name in FACTOR_NAMES
                if build_result.factor_values[factor_name].availability
                is FactorAvailability.AVAILABLE
            ]
        )
        transition_reason = (
            "Initial Early Bird assessment classified the situation as {0}."
            .format(emerging_situation.stage.value)
        )
        entry = MarketSituationTimelineEntry(
            entry_id=normalized_entry_id,
            timeline_id=normalized_timeline_id,
            created_at=created_at,
            stage=emerging_situation.stage,
            dna=dna,
            supporting_factors=emerging_situation.supporting_factors,
            limiting_factors=emerging_situation.limiting_factors,
            expected_events=(),
            observed_events=observed_events,
            missing_expected_events=(),
            unexpected_events=(),
            transition_reason=transition_reason,
            source_assessment_id=assessment.assessment_id,
            source_candidate_id=candidate.candidate_id,
            source_situation_id=None,
            metadata={
                "adapter_version": ADAPTER_VERSION,
                "source": candidate.source,
                "timeframe": scan_item.timeframe,
                "rank": assessment.rank,
            },
        )
        timeline = MarketSituationTimeline(
            timeline_id=normalized_timeline_id,
            asset=assessment.asset,
            created_at=created_at,
            updated_at=created_at,
            entries=(entry,),
            current_stage=emerging_situation.stage,
            version=1,
            metadata={
                "phase": "PS-4 Step 2",
                "identity_policy": "caller-supplied-run-local",
                "source": candidate.source,
                "timeframe": scan_item.timeframe,
            },
        )
        return EarlyBirdTimelineResult(
            timeline=timeline,
            explanation=explanation,
            emerging_situation=emerging_situation,
            source_assessment_id=assessment.assessment_id,
            source_candidate_id=candidate.candidate_id,
            created_at=created_at,
            metadata={
                "adapter_version": ADAPTER_VERSION,
                "persistence": "none",
            },
        )

    @staticmethod
    def _validate_inputs(
        scan_item: Any,
        explanation: Any,
        emerging_situation: Any,
    ) -> Tuple[Any, Any, Any]:
        _attributes(
            scan_item,
            ("assessment", "build_result", "symbol", "timeframe", "scanned_at"),
            "scan_item",
        )
        assessment = scan_item.assessment
        build_result = scan_item.build_result
        _attributes(
            assessment,
            ("assessment_id", "candidate_id", "asset", "metadata"),
            "assessment",
        )
        _attributes(build_result, ("candidate", "factor_values", "metadata"), "build_result")
        candidate = build_result.candidate
        _attributes(
            candidate,
            (
                "candidate_id",
                "asset",
                "source",
                "quality",
                "freshness_score",
                "data_completeness_score",
                "fast_event_ids",
                "observation_ids",
            ),
            "candidate",
        )
        if not isinstance(explanation, EarlyBirdExplanation):
            raise TypeError("explanation must be an EarlyBirdExplanation")
        if not isinstance(emerging_situation, EmergingSituation):
            raise TypeError("emerging_situation must be an EmergingSituation")
        assets = {
            _required_text(scan_item.symbol, "scan item asset").upper(),
            _required_text(assessment.asset, "assessment asset").upper(),
            _required_text(candidate.asset, "candidate asset").upper(),
            explanation.asset,
            emerging_situation.asset,
        }
        if len(assets) != 1:
            raise ValueError("all Early Bird input assets must match")
        if assessment.candidate_id != candidate.candidate_id:
            raise ValueError("assessment and build result candidate IDs must match")
        if explanation.metadata.get("candidate_id") != candidate.candidate_id:
            raise ValueError("explanation candidate identity must match")
        if emerging_situation.source_candidate_id != candidate.candidate_id:
            raise ValueError("emerging situation candidate identity must match")
        if explanation.metadata.get("assessment_id") != assessment.assessment_id:
            raise ValueError("explanation assessment identity must match")
        if emerging_situation.source_assessment_id != assessment.assessment_id:
            raise ValueError("emerging situation assessment identity must match")
        return assessment, build_result, candidate

    @staticmethod
    def _situation_dna(
        scan_item: Any,
        explanation: EarlyBirdExplanation,
        emerging_situation: EmergingSituation,
    ) -> SituationDNA:
        assessment = scan_item.assessment
        build_result = scan_item.build_result
        candidate = build_result.candidate
        values = build_result.factor_values
        factor_scores = {
            factor_name: (
                values[factor_name].score
                if values[factor_name].availability is FactorAvailability.AVAILABLE
                else None
            )
            for factor_name in FACTOR_NAMES
        }
        availability = {
            factor_name: values[factor_name].availability.value
            for factor_name in FACTOR_NAMES
        }
        return SituationDNA(
            completeness=candidate.data_completeness_score,
            quality=candidate.quality,
            freshness=candidate.freshness_score,
            opportunity=assessment.opportunity_score,
            priority=assessment.priority_score,
            maturity=assessment.maturity_score,
            emergence=emerging_situation.emergence_score,
            horizon=emerging_situation.horizon_score,
            detection_confidence=emerging_situation.detection_confidence,
            factor_availability=availability,
            metadata={
                "source": candidate.source,
                "timeframe": scan_item.timeframe,
                "assessment_id": assessment.assessment_id,
                "candidate_id": candidate.candidate_id,
                "source_event_ids": list(candidate.fast_event_ids),
                "source_observation_ids": list(candidate.observation_ids),
                "policy_version": assessment.metadata.get("policy_version"),
                "explanation_version": explanation.metadata.get(
                    "explanation_version"
                ),
                "emerging_version": emerging_situation.metadata.get(
                    "emerging_version"
                ),
                "builder_policy": build_result.metadata.get("builder_policy"),
            },
            **factor_scores
        )


def build_timelines_from_scan(
    scan_result: Any,
    *,
    adapter: Optional[EarlyBirdTimelineAdapter] = None,
    explainer: Optional[EarlyBirdExplainer] = None,
    emerging_engine: Optional[EmergingSituationEngine] = None,
    id_builder: Callable[[Any], Tuple[str, str]] = deterministic_run_local_ids,
) -> EarlyBirdTimelineBatchResult:
    """Build independent in-memory Timeline v1 results for ranked scan items."""

    _attributes(scan_result, ("items",), "scan_result")
    if isinstance(scan_result.items, (str, bytes, set, frozenset)):
        raise TypeError("scan_result.items must be an ordered collection")
    items = tuple(scan_result.items)
    timeline_adapter = adapter or EarlyBirdTimelineAdapter()
    explanation_engine = explainer or EarlyBirdExplainer()
    situation_engine = emerging_engine or EmergingSituationEngine()
    results = []
    errors = {}
    previous_item = None
    previous_explanation_valid = False

    for item in items:
        asset = getattr(item, "symbol", "UNKNOWN")
        try:
            previous_assessment = None
            previous_build_result = None
            if previous_item is not None and previous_explanation_valid:
                previous_assessment = previous_item.assessment
                previous_build_result = previous_item.build_result
            explanation = explanation_engine.explain(
                item.assessment,
                item.build_result,
                previous_assessment=previous_assessment,
                previous_build_result=previous_build_result,
            )
            previous_explanation_valid = True
            emerging = situation_engine.evaluate(
                item.assessment,
                item.build_result,
                explanation,
            )
            timeline_id, entry_id = id_builder(item)
            results.append(
                timeline_adapter.create_timeline(
                    scan_item=item,
                    explanation=explanation,
                    emerging_situation=emerging,
                    timeline_id=timeline_id,
                    entry_id=entry_id,
                )
            )
        except Exception as exc:
            errors[_required_text(asset, "failed asset").upper()] = _error_text(exc)
            previous_explanation_valid = False
        previous_item = item

    distribution = {}
    for stage in EmergingStage:
        count = sum(result.timeline.current_stage is stage for result in results)
        if count:
            distribution[stage.value] = count
    return EarlyBirdTimelineBatchResult(
        results=tuple(results),
        errors=errors,
        stage_distribution=distribution,
        top_assets=tuple(result.timeline.asset for result in results),
    )


def format_early_bird_timeline(result: EarlyBirdTimelineResult) -> str:
    """Format one Timeline result as plain descriptive terminal text."""

    if not isinstance(result, EarlyBirdTimelineResult):
        raise TypeError("result must be an EarlyBirdTimelineResult")
    timeline = result.timeline
    entry = timeline.entries[0]
    dna = entry.dna
    lines = [
        "Asset: {0}".format(timeline.asset),
        "Timeline: {0}".format(timeline.timeline_id),
        "Version: {0}".format(timeline.version),
        "Stage: {0}".format(timeline.current_stage.value),
        "",
        "Opportunity: {0:.2f}".format(dna.opportunity),
        "Priority: {0:.2f}".format(dna.priority),
        "Maturity: {0:.2f}".format(dna.maturity),
        "Emergence: {0:.2f}".format(dna.emergence),
        "Horizon: {0:.2f}".format(dna.horizon),
        "Detection confidence: {0:.2f}".format(dna.detection_confidence),
        "",
        "Situation DNA:",
    ]
    for factor_name in FACTOR_NAMES:
        score = getattr(dna, factor_name)
        display = (
            "{0:.2f}".format(score)
            if score is not None
            else dna.factor_availability[factor_name]
        )
        lines.append("- {0}: {1}".format(FACTOR_LABELS[factor_name], display))
    lines.extend(("", "Timeline:"))
    for timeline_entry in timeline.entries:
        lines.append(
            "- {0} — {1}".format(
                timeline_entry.created_at.isoformat(),
                timeline_entry.transition_reason,
            )
        )
    return "\n".join(lines)


__all__ = [
    "EarlyBirdTimelineAdapter",
    "EarlyBirdTimelineBatchResult",
    "EarlyBirdTimelineResult",
    "build_timelines_from_scan",
    "deterministic_run_local_ids",
    "format_early_bird_timeline",
]
