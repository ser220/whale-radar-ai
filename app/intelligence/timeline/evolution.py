"""Deterministic in-memory evolution of Market Situation timelines."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import math
from numbers import Real
from types import MappingProxyType
from typing import Any, Dict, Iterable, Mapping as TypingMapping, Optional, Tuple

from app.intelligence.early_bird import EmergingStage
from app.intelligence.timeline.identity import (
    DEFAULT_MATCH_THRESHOLD,
    IDENTITY_POLICY_VERSION,
    SituationIdentityEngine,
    SituationIdentityResult,
)
from app.intelligence.timeline.models import (
    MarketSituationTimeline,
    MarketSituationTimelineEntry,
    SituationDNA,
)
from app.intelligence.timeline.timeline import append_timeline_entry


EVOLUTION_VERSION = 1

DNA_FACTOR_FIELDS = (
    "whale_activity",
    "funding_divergence",
    "volume_expansion",
    "structure_event",
    "momentum_shift",
    "relative_strength",
    "open_interest_change",
    "liquidity_event",
)

DNA_SCORE_FIELDS = (
    "completeness",
    "quality",
    "freshness",
    "opportunity",
    "priority",
    "maturity",
    "emergence",
    "horizon",
    "detection_confidence",
)

DNA_FIELDS = DNA_FACTOR_FIELDS + DNA_SCORE_FIELDS

DNA_LABELS = MappingProxyType({
    "whale_activity": "Whale Activity",
    "funding_divergence": "Funding Divergence",
    "volume_expansion": "Volume Expansion",
    "structure_event": "Structure Event",
    "momentum_shift": "Momentum Shift",
    "relative_strength": "Relative Strength",
    "open_interest_change": "Open Interest Change",
    "liquidity_event": "Liquidity Event",
    "completeness": "Completeness",
    "quality": "Quality",
    "freshness": "Freshness",
    "opportunity": "Opportunity",
    "priority": "Priority",
    "maturity": "Maturity",
    "emergence": "Emergence",
    "horizon": "Horizon",
    "detection_confidence": "Detection Confidence",
})


class EvolutionAction(str, Enum):
    """Descriptive action taken for one candidate timeline."""

    CREATED = "CREATED"
    CONTINUED = "CONTINUED"


class DeltaState(str, Enum):
    """Availability-aware relationship between two point-in-time DNA values."""

    UNCHANGED = "UNCHANGED"
    CHANGED = "CHANGED"
    APPEARED = "APPEARED"
    BECAME_UNAVAILABLE = "BECAME_UNAVAILABLE"


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{0} must be a string".format(field_name))
    normalized = value.strip()
    if not normalized:
        raise ValueError("{0} must not be empty".format(field_name))
    return normalized


def _optional_text(value: Any, field_name: str) -> Optional[str]:
    if value is None:
        return None
    return _required_text(value, field_name)


def _optional_version(value: Any, field_name: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{0} must be an integer or None".format(field_name))
    if value < 1:
        raise ValueError("{0} must be at least 1".format(field_name))
    return value


def _utc_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("{0} must be a datetime".format(field_name))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("{0} must be timezone-aware".format(field_name))
    return value.astimezone(timezone.utc)


def _parse_datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return _utc_datetime(value, field_name)
    if not isinstance(value, str):
        raise TypeError("{0} must be a datetime or ISO-8601 string".format(field_name))
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("{0} must be a valid ISO-8601 datetime".format(field_name)) from exc
    return _utc_datetime(parsed, field_name)


def _optional_number(value: Any, field_name: str) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{0} must be a real number or None".format(field_name))
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError("{0} must be finite".format(field_name))
    return normalized


def _freeze(value: Any, field_name: str = "metadata") -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("{0} numeric values must be finite".format(field_name))
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return _utc_datetime(value, field_name).isoformat()
    if isinstance(value, Mapping):
        items = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("{0} keys must be strings".format(field_name))
            items.append((key, _freeze(item, field_name)))
        items.sort(key=lambda pair: pair[0])
        return MappingProxyType(dict(items))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item, field_name) for item in value)
    if isinstance(value, (set, frozenset)):
        return tuple(sorted((_freeze(item, field_name) for item in value), key=repr))
    if isinstance(value, Real):
        normalized = float(value)
        if not math.isfinite(normalized):
            raise ValueError("{0} numeric values must be finite".format(field_name))
        return normalized
    raise TypeError("{0} values must be serializable primitives".format(field_name))


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return _utc_datetime(value, "timestamp").isoformat()
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _mapping_payload(value: Any, model_name: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("{0} data must be a mapping".format(model_name))
    return dict(value)


def _sanitize_error(exc: Exception) -> str:
    message = str(exc).strip() or "No error detail was provided."
    return "{0}: {1}".format(type(exc).__name__, message)


@dataclass(frozen=True)
class SituationDNADelta:
    """One deterministic, non-directional change between SituationDNA values."""

    field_name: str
    previous_value: Optional[float]
    current_value: Optional[float]
    numeric_delta: Optional[float]
    state: DeltaState
    previous_availability: Optional[str] = None
    current_availability: Optional[str] = None
    availability_changed: bool = False

    def __post_init__(self) -> None:
        field_name = _required_text(self.field_name, "field_name")
        if field_name not in DNA_FIELDS:
            raise ValueError("unsupported SituationDNA field: {0}".format(field_name))
        object.__setattr__(self, "field_name", field_name)
        object.__setattr__(
            self,
            "previous_value",
            _optional_number(self.previous_value, "previous_value"),
        )
        object.__setattr__(
            self,
            "current_value",
            _optional_number(self.current_value, "current_value"),
        )
        object.__setattr__(
            self,
            "numeric_delta",
            _optional_number(self.numeric_delta, "numeric_delta"),
        )
        try:
            state = self.state if isinstance(self.state, DeltaState) else DeltaState(self.state)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid delta state: {0!r}".format(self.state)) from exc
        object.__setattr__(self, "state", state)
        object.__setattr__(
            self,
            "previous_availability",
            _optional_text(self.previous_availability, "previous_availability"),
        )
        object.__setattr__(
            self,
            "current_availability",
            _optional_text(self.current_availability, "current_availability"),
        )
        if not isinstance(self.availability_changed, bool):
            raise TypeError("availability_changed must be a boolean")
        expected_state = _delta_state(self.previous_value, self.current_value)
        if state is not expected_state:
            raise ValueError("state must match previous and current values")
        expected_delta = (
            round(self.current_value - self.previous_value, 6)
            if self.previous_value is not None and self.current_value is not None
            else None
        )
        if self.numeric_delta != expected_delta:
            raise ValueError("numeric_delta must match measured values")
        expected_availability_change = (
            self.previous_availability != self.current_availability
        )
        if self.availability_changed != expected_availability_change:
            raise ValueError("availability_changed must match availability values")

    @property
    def material(self) -> bool:
        return self.state is not DeltaState.UNCHANGED or self.availability_changed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "previous_value": self.previous_value,
            "current_value": self.current_value,
            "numeric_delta": self.numeric_delta,
            "state": self.state.value,
            "previous_availability": self.previous_availability,
            "current_availability": self.current_availability,
            "availability_changed": self.availability_changed,
        }

    @classmethod
    def from_dict(cls, data: TypingMapping[str, Any]) -> "SituationDNADelta":
        return cls(**_mapping_payload(data, "SituationDNA delta"))


def _delta_state(previous: Optional[float], current: Optional[float]) -> DeltaState:
    if previous is None and current is not None:
        return DeltaState.APPEARED
    if previous is not None and current is None:
        return DeltaState.BECAME_UNAVAILABLE
    if previous is None and current is None:
        return DeltaState.UNCHANGED
    return DeltaState.UNCHANGED if previous == current else DeltaState.CHANGED


def extract_situation_dna_deltas(
    previous: SituationDNA,
    current: SituationDNA,
) -> Tuple[SituationDNADelta, ...]:
    """Compare all approved DNA fields without directional interpretation."""

    if not isinstance(previous, SituationDNA):
        raise TypeError("previous must be a SituationDNA")
    if not isinstance(current, SituationDNA):
        raise TypeError("current must be a SituationDNA")
    deltas = []
    for field_name in DNA_FIELDS:
        previous_value = getattr(previous, field_name)
        current_value = getattr(current, field_name)
        numeric_delta = (
            round(current_value - previous_value, 6)
            if previous_value is not None and current_value is not None
            else None
        )
        previous_availability = (
            previous.factor_availability.get(field_name)
            if field_name in DNA_FACTOR_FIELDS
            else None
        )
        current_availability = (
            current.factor_availability.get(field_name)
            if field_name in DNA_FACTOR_FIELDS
            else None
        )
        deltas.append(
            SituationDNADelta(
                field_name=field_name,
                previous_value=previous_value,
                current_value=current_value,
                numeric_delta=numeric_delta,
                state=_delta_state(previous_value, current_value),
                previous_availability=previous_availability,
                current_availability=current_availability,
                availability_changed=(
                    previous_availability != current_availability
                ),
            )
        )
    return tuple(deltas)


@dataclass(frozen=True)
class SituationEvolutionDecision:
    """Immutable trace for one CREATED or CONTINUED evolution action."""

    asset: str
    identity_result: SituationIdentityResult
    action: EvolutionAction
    previous_timeline_id: Optional[str]
    previous_version: Optional[int]
    result_timeline_id: str
    result_version: int
    previous_stage: Optional[EmergingStage]
    new_stage: EmergingStage
    stage_changed: bool
    created_at: datetime
    reason: str
    metadata: TypingMapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "asset", _required_text(self.asset, "asset").upper())
        if not isinstance(self.identity_result, SituationIdentityResult):
            raise TypeError("identity_result must be a SituationIdentityResult")
        try:
            action = self.action if isinstance(self.action, EvolutionAction) else EvolutionAction(self.action)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid evolution action: {0!r}".format(self.action)) from exc
        object.__setattr__(self, "action", action)
        object.__setattr__(
            self,
            "previous_timeline_id",
            _optional_text(self.previous_timeline_id, "previous_timeline_id"),
        )
        object.__setattr__(
            self,
            "previous_version",
            _optional_version(self.previous_version, "previous_version"),
        )
        object.__setattr__(
            self,
            "result_timeline_id",
            _required_text(self.result_timeline_id, "result_timeline_id"),
        )
        result_version = _optional_version(self.result_version, "result_version")
        object.__setattr__(self, "result_version", result_version)
        previous_stage = self.previous_stage
        if previous_stage is not None and not isinstance(previous_stage, EmergingStage):
            try:
                previous_stage = EmergingStage(previous_stage)
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid previous_stage") from exc
        object.__setattr__(self, "previous_stage", previous_stage)
        new_stage = self.new_stage
        if not isinstance(new_stage, EmergingStage):
            try:
                new_stage = EmergingStage(new_stage)
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid new_stage") from exc
        object.__setattr__(self, "new_stage", new_stage)
        if not isinstance(self.stage_changed, bool):
            raise TypeError("stage_changed must be a boolean")
        expected_stage_changed = previous_stage is not None and previous_stage is not new_stage
        if self.stage_changed != expected_stage_changed:
            raise ValueError("stage_changed must match previous and new stages")
        object.__setattr__(self, "created_at", _utc_datetime(self.created_at, "created_at"))
        object.__setattr__(self, "reason", _required_text(self.reason, "reason"))
        object.__setattr__(self, "metadata", _freeze(self.metadata, "metadata"))
        if (self.previous_timeline_id is None) != (self.previous_version is None):
            raise ValueError("previous timeline ID and version must be provided together")
        if action is EvolutionAction.CONTINUED:
            if self.previous_timeline_id is None:
                raise ValueError("CONTINUED requires a previous timeline")
            if not self.identity_result.matched:
                raise ValueError("CONTINUED requires a matched identity result")
            if self.result_timeline_id != self.previous_timeline_id:
                raise ValueError("CONTINUED must preserve timeline ID")
            if self.result_version != self.previous_version + 1:
                raise ValueError("CONTINUED must increment version exactly once")
        elif self.result_version != 1:
            raise ValueError("CREATED result must remain version 1")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "identity_result": self.identity_result.to_dict(),
            "action": self.action.value,
            "previous_timeline_id": self.previous_timeline_id,
            "previous_version": self.previous_version,
            "result_timeline_id": self.result_timeline_id,
            "result_version": self.result_version,
            "previous_stage": (
                self.previous_stage.value if self.previous_stage is not None else None
            ),
            "new_stage": self.new_stage.value,
            "stage_changed": self.stage_changed,
            "created_at": self.created_at.isoformat(),
            "reason": self.reason,
            "metadata": _plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: TypingMapping[str, Any]) -> "SituationEvolutionDecision":
        payload = _mapping_payload(data, "situation evolution decision")
        payload["identity_result"] = SituationIdentityResult.from_dict(
            payload.get("identity_result")
        )
        payload["created_at"] = _parse_datetime(payload.get("created_at"), "created_at")
        return cls(**payload)


@dataclass(frozen=True)
class SituationEvolutionBatchResult:
    """Immutable result of evolving one process-local scan batch."""

    active_timelines: TypingMapping[str, MarketSituationTimeline]
    decisions: Tuple[SituationEvolutionDecision, ...]
    errors: TypingMapping[str, str]
    first_scan_at: datetime
    second_scan_at: datetime
    metadata: TypingMapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.active_timelines, Mapping):
            raise TypeError("active_timelines must be a mapping")
        active = {}
        for asset, timeline in self.active_timelines.items():
            normalized_asset = _required_text(asset, "active timeline asset").upper()
            if not isinstance(timeline, MarketSituationTimeline):
                raise TypeError("active timeline values must be MarketSituationTimeline")
            if timeline.asset != normalized_asset:
                raise ValueError("active timeline key must match timeline asset")
            active[normalized_asset] = timeline
        object.__setattr__(
            self,
            "active_timelines",
            MappingProxyType(dict(sorted(active.items()))),
        )
        if isinstance(self.decisions, (str, bytes, set, frozenset)):
            raise TypeError("decisions must be an ordered collection")
        decisions = tuple(self.decisions)
        if not all(isinstance(item, SituationEvolutionDecision) for item in decisions):
            raise TypeError("decisions must contain SituationEvolutionDecision objects")
        if tuple(item.asset for item in decisions) != tuple(sorted(item.asset for item in decisions)):
            raise ValueError("decisions must be ordered deterministically by asset")
        object.__setattr__(self, "decisions", decisions)
        if not isinstance(self.errors, Mapping):
            raise TypeError("errors must be a mapping")
        errors = {
            _required_text(asset, "error asset").upper(): _required_text(message, "error message")
            for asset, message in self.errors.items()
        }
        object.__setattr__(self, "errors", MappingProxyType(dict(sorted(errors.items()))))
        first_scan_at = _utc_datetime(self.first_scan_at, "first_scan_at")
        second_scan_at = _utc_datetime(self.second_scan_at, "second_scan_at")
        if second_scan_at < first_scan_at:
            raise ValueError("second_scan_at must not precede first_scan_at")
        object.__setattr__(self, "first_scan_at", first_scan_at)
        object.__setattr__(self, "second_scan_at", second_scan_at)
        object.__setattr__(self, "metadata", _freeze(self.metadata, "metadata"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_timelines": {
                asset: timeline.to_dict()
                for asset, timeline in self.active_timelines.items()
            },
            "decisions": [decision.to_dict() for decision in self.decisions],
            "errors": dict(self.errors),
            "first_scan_at": self.first_scan_at.isoformat(),
            "second_scan_at": self.second_scan_at.isoformat(),
            "metadata": _plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: TypingMapping[str, Any]) -> "SituationEvolutionBatchResult":
        payload = _mapping_payload(data, "situation evolution batch result")
        raw_timelines = payload.get("active_timelines")
        if not isinstance(raw_timelines, Mapping):
            raise TypeError("active_timelines must be a mapping")
        payload["active_timelines"] = {
            asset: MarketSituationTimeline.from_dict(timeline)
            for asset, timeline in raw_timelines.items()
        }
        payload["decisions"] = tuple(
            SituationEvolutionDecision.from_dict(decision)
            for decision in payload.get("decisions", ())
        )
        payload["first_scan_at"] = _parse_datetime(
            payload.get("first_scan_at"), "first_scan_at"
        )
        payload["second_scan_at"] = _parse_datetime(
            payload.get("second_scan_at"), "second_scan_at"
        )
        return cls(**payload)


class SituationEvolutionEngine:
    """Evolve independent candidate Timeline v1 objects against active state."""

    def __init__(self, identity_engine: Optional[SituationIdentityEngine] = None) -> None:
        if identity_engine is not None and not isinstance(identity_engine, SituationIdentityEngine):
            raise TypeError("identity_engine must be a SituationIdentityEngine")
        self._identity_engine = identity_engine or SituationIdentityEngine()

    def evolve(
        self,
        *,
        existing_timelines: TypingMapping[str, MarketSituationTimeline],
        candidate_timelines: Iterable[MarketSituationTimeline],
        updated_at: datetime,
        first_scan_at: Optional[datetime] = None
    ) -> SituationEvolutionBatchResult:
        normalized_updated_at = _utc_datetime(updated_at, "updated_at")
        active = self._existing_timelines(existing_timelines)
        initial_active = dict(active)
        candidates, candidate_errors = self._candidate_timelines(candidate_timelines)
        decisions = []
        errors = dict(candidate_errors)

        for candidate in candidates:
            asset = candidate.asset
            try:
                existing = active.get(asset)
                if existing is None:
                    identity_result = self._not_evaluated_identity(candidate)
                    result_timeline = candidate
                    action = EvolutionAction.CREATED
                    deltas = ()
                else:
                    identity_result = self._identity_engine.evaluate(existing, candidate)
                    deltas = extract_situation_dna_deltas(
                        existing.entries[-1].dna,
                        candidate.entries[0].dna,
                    )
                    if identity_result.matched:
                        copied_entry = self._copy_entry_for_continuation(
                            candidate.entries[0],
                            existing.timeline_id,
                            identity_result,
                        )
                        result_timeline = append_timeline_entry(
                            existing,
                            copied_entry,
                            updated_at=normalized_updated_at,
                        )
                        action = EvolutionAction.CONTINUED
                    else:
                        result_timeline = candidate
                        action = EvolutionAction.CREATED

                decisions.append(
                    self._decision(
                        existing=existing,
                        candidate=candidate,
                        result=result_timeline,
                        identity_result=identity_result,
                        action=action,
                        deltas=deltas,
                        created_at=normalized_updated_at,
                    )
                )
                active[asset] = result_timeline
            except Exception as exc:
                errors[asset] = _sanitize_error(exc)

        derived_first_scan_at = self._first_scan_at(
            existing_timelines=initial_active,
            explicit=first_scan_at,
            fallback=normalized_updated_at,
        )
        return SituationEvolutionBatchResult(
            active_timelines=active,
            decisions=tuple(decisions),
            errors=errors,
            first_scan_at=derived_first_scan_at,
            second_scan_at=normalized_updated_at,
            metadata={
                "evolution_version": EVOLUTION_VERSION,
                "persistence": "none",
                "candidate_count": len(candidates) + len(candidate_errors),
                "successful_count": len(decisions),
                "error_count": len(errors),
            },
        )

    @staticmethod
    def _existing_timelines(
        values: TypingMapping[str, MarketSituationTimeline]
    ) -> Dict[str, MarketSituationTimeline]:
        if not isinstance(values, Mapping):
            raise TypeError("existing_timelines must be a mapping")
        normalized = {}
        for key, timeline in values.items():
            asset = _required_text(key, "existing timeline asset").upper()
            if key != asset:
                raise ValueError("existing timeline mapping keys must be normalized")
            if not isinstance(timeline, MarketSituationTimeline):
                raise TypeError("existing timeline values must be MarketSituationTimeline")
            if timeline.asset != asset:
                raise ValueError("existing timeline key must match timeline asset")
            normalized[asset] = timeline
        return dict(sorted(normalized.items()))

    @staticmethod
    def _candidate_timelines(
        values: Iterable[MarketSituationTimeline]
    ) -> Tuple[Tuple[MarketSituationTimeline, ...], Dict[str, str]]:
        if isinstance(values, (str, bytes, set, frozenset)):
            raise TypeError("candidate_timelines must be an ordered iterable")
        try:
            materialized = tuple(values)
        except TypeError as exc:
            raise TypeError("candidate_timelines must be iterable") from exc
        by_asset = {}
        errors = {}
        for index, timeline in enumerate(materialized):
            if not isinstance(timeline, MarketSituationTimeline):
                errors["CANDIDATE-{0}".format(index + 1)] = (
                    "TypeError: candidate must be a MarketSituationTimeline"
                )
                continue
            asset = timeline.asset
            if asset in by_asset:
                errors[asset] = "ValueError: duplicate candidate asset"
                by_asset[asset] = None
                continue
            by_asset[asset] = timeline
        candidates = []
        for asset in sorted(by_asset):
            timeline = by_asset[asset]
            if timeline is None:
                continue
            if timeline.version != 1:
                errors[asset] = "ValueError: candidate timeline must be version 1"
                continue
            if len(timeline.entries) != 1:
                errors[asset] = (
                    "ValueError: candidate timeline must contain exactly one entry"
                )
                continue
            candidates.append(timeline)
        return tuple(candidates), errors

    @staticmethod
    def _copy_entry_for_continuation(
        candidate: MarketSituationTimelineEntry,
        timeline_id: str,
        identity_result: SituationIdentityResult,
    ) -> MarketSituationTimelineEntry:
        metadata = _plain(candidate.metadata)
        metadata["identity_provenance"] = identity_result.to_dict()
        return MarketSituationTimelineEntry(
            entry_id=candidate.entry_id,
            timeline_id=timeline_id,
            created_at=candidate.created_at,
            stage=candidate.stage,
            dna=candidate.dna,
            supporting_factors=candidate.supporting_factors,
            limiting_factors=candidate.limiting_factors,
            expected_events=candidate.expected_events,
            observed_events=candidate.observed_events,
            missing_expected_events=candidate.missing_expected_events,
            unexpected_events=candidate.unexpected_events,
            transition_reason=candidate.transition_reason,
            source_assessment_id=candidate.source_assessment_id,
            source_candidate_id=candidate.source_candidate_id,
            source_situation_id=candidate.source_situation_id,
            metadata=metadata,
        )

    @staticmethod
    def _not_evaluated_identity(
        candidate: MarketSituationTimeline,
    ) -> SituationIdentityResult:
        return SituationIdentityResult(
            matched=False,
            confidence=0.0,
            reason="No active timeline exists for this asset; a new situation was created.",
            matched_timeline_id=None,
            matched_version=None,
            candidate_timeline_id=candidate.timeline_id,
            metadata={
                "identity_policy_version": IDENTITY_POLICY_VERSION,
                "decision": "new_situation",
                "evaluation_performed": False,
                "hard_rejection": False,
                "criteria": {},
                "match_threshold": DEFAULT_MATCH_THRESHOLD,
                "time_gap_seconds": None,
                "existing_stage": None,
                "candidate_stage": candidate.current_stage.value,
                "confidence_semantics": "identity_match_continuity",
            },
        )

    @staticmethod
    def _decision(
        *,
        existing: Optional[MarketSituationTimeline],
        candidate: MarketSituationTimeline,
        result: MarketSituationTimeline,
        identity_result: SituationIdentityResult,
        action: EvolutionAction,
        deltas: Tuple[SituationDNADelta, ...],
        created_at: datetime
    ) -> SituationEvolutionDecision:
        previous_stage = existing.current_stage if existing is not None else None
        return SituationEvolutionDecision(
            asset=candidate.asset,
            identity_result=identity_result,
            action=action,
            previous_timeline_id=(existing.timeline_id if existing is not None else None),
            previous_version=(existing.version if existing is not None else None),
            result_timeline_id=result.timeline_id,
            result_version=result.version,
            previous_stage=previous_stage,
            new_stage=candidate.current_stage,
            stage_changed=(
                previous_stage is not None
                and previous_stage is not candidate.current_stage
            ),
            created_at=created_at,
            reason=identity_result.reason,
            metadata={
                "evolution_version": EVOLUTION_VERSION,
                "identity_trace": identity_result.to_dict(),
                "dna_deltas": [delta.to_dict() for delta in deltas],
                "previous_timeline_preserved": existing is not None,
                "candidate_timeline_unchanged": True,
            },
        )

    @staticmethod
    def _first_scan_at(
        *,
        existing_timelines: TypingMapping[str, MarketSituationTimeline],
        explicit: Optional[datetime],
        fallback: datetime
    ) -> datetime:
        if explicit is not None:
            return _utc_datetime(explicit, "first_scan_at")
        if existing_timelines:
            return min(timeline.updated_at for timeline in existing_timelines.values())
        return fallback


def format_situation_evolution(decision: SituationEvolutionDecision) -> str:
    """Format one evolution decision as plain, non-trading terminal text."""

    if not isinstance(decision, SituationEvolutionDecision):
        raise TypeError("decision must be a SituationEvolutionDecision")
    previous_version = (
        str(decision.previous_version)
        if decision.previous_version is not None
        else "None"
    )
    previous_stage = (
        decision.previous_stage.value
        if decision.previous_stage is not None
        else "None"
    )
    lines = [
        decision.asset,
        "",
        "Action: {0}".format(decision.action.value),
        "Timeline: {0}".format(decision.result_timeline_id),
        "Version: {0} -> {1}".format(previous_version, decision.result_version),
        "Stage: {0} -> {1}".format(previous_stage, decision.new_stage.value),
        "Identity confidence: {0:.2f}".format(decision.identity_result.confidence),
        "",
        "Key changes:",
    ]
    raw_deltas = decision.metadata.get("dna_deltas", ())
    deltas = tuple(SituationDNADelta.from_dict(item) for item in raw_deltas)
    material = tuple(delta for delta in deltas if delta.material)
    if not material:
        lines.append("- No material DNA changes")
    else:
        for delta in material:
            label = DNA_LABELS[delta.field_name]
            if delta.state is DeltaState.APPEARED:
                text = "APPEARED ({0:g})".format(delta.current_value)
            elif delta.state is DeltaState.BECAME_UNAVAILABLE:
                text = "BECAME_UNAVAILABLE (was {0:g})".format(delta.previous_value)
            else:
                text = "{0:g} -> {1:g}".format(
                    delta.previous_value,
                    delta.current_value,
                )
            lines.append("- {0}: {1}".format(label, text))
            if delta.availability_changed:
                lines.append(
                    "  Availability: {0} -> {1}".format(
                        delta.previous_availability or "None",
                        delta.current_availability or "None",
                    )
                )
    lines.extend(["", "Identity:"])
    metadata = decision.identity_result.metadata
    criteria = metadata.get("criteria", {})
    if criteria:
        for name in (
            "time_continuity",
            "dna_continuity",
            "stage_compatibility",
            "supporting_factor_continuity",
            "limiting_factor_continuity",
            "evolution_continuity",
        ):
            if name in criteria:
                lines.append(
                    "- {0}: {1:.2f}".format(
                        name.replace("_", " ").title(),
                        criteria[name],
                    )
                )
    elif metadata.get("hard_rejection"):
        lines.append(
            "- Hard rejection: {0}".format(
                metadata.get("rejection_code", "unspecified")
            )
        )
    else:
        lines.append("- Identity comparison was not required")
    lines.append("- Reason: {0}".format(decision.reason))
    return "\n".join(lines)


def format_situation_evolution_batch(
    result: SituationEvolutionBatchResult,
) -> str:
    """Format one two-scan in-memory evolution batch."""

    if not isinstance(result, SituationEvolutionBatchResult):
        raise TypeError("result must be a SituationEvolutionBatchResult")
    created = sum(item.action is EvolutionAction.CREATED for item in result.decisions)
    continued = sum(item.action is EvolutionAction.CONTINUED for item in result.decisions)
    lines = [
        "Market Situation Evolution",
        "First scan: {0}".format(result.first_scan_at.isoformat()),
        "Second scan: {0}".format(result.second_scan_at.isoformat()),
        "Created: {0}".format(created),
        "Continued: {0}".format(continued),
        "Failed: {0}".format(len(result.errors)),
    ]
    for decision in result.decisions:
        lines.extend(["", format_situation_evolution(decision)])
    if result.errors:
        lines.extend(["", "Evolution errors:"])
        for asset, error in result.errors.items():
            lines.append("- {0}: {1}".format(asset, error))
    return "\n".join(lines)


__all__ = [
    "DeltaState",
    "EvolutionAction",
    "SituationDNADelta",
    "SituationEvolutionBatchResult",
    "SituationEvolutionDecision",
    "SituationEvolutionEngine",
    "extract_situation_dna_deltas",
    "format_situation_evolution",
    "format_situation_evolution_batch",
]
