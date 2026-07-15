"""Deterministic evaluation of immutable Market Situation expectations."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import math
from numbers import Real
from types import MappingProxyType
from typing import Any, Dict, Mapping as TypingMapping, Optional, Tuple

from app.intelligence.early_bird import EmergingStage
from app.intelligence.timeline.expectations import (
    ExpectationKind,
    SituationExpectation,
)
from app.intelligence.timeline.models import (
    MarketSituationTimeline,
    MarketSituationTimelineEntry,
)


EVALUATION_POLICY_VERSION = 1
SUPPORTED_EVALUATION_CONTRACT_VERSION = "1"

FACTOR_FIELDS = (
    "whale_activity",
    "funding_divergence",
    "volume_expansion",
    "structure_event",
    "momentum_shift",
    "relative_strength",
    "open_interest_change",
    "liquidity_event",
)

INITIATING_FACTORS = (
    "whale_activity",
    "funding_divergence",
    "structure_event",
    "volume_expansion",
)

_STAGE_INDEX = MappingProxyType({
    EmergingStage.UNKNOWN: -1,
    EmergingStage.SEED: 0,
    EmergingStage.EMERGING: 1,
    EmergingStage.BUILDING: 2,
    EmergingStage.MATURE: 3,
    EmergingStage.EXHAUSTED: 4,
})


class ExpectationEvaluationStatus(str, Enum):
    """Classification of evidence inside one expectation window."""

    PENDING = "PENDING"
    FULFILLED = "FULFILLED"
    MISSING = "MISSING"
    CONTRADICTED = "CONTRADICTED"
    EXPIRED = "EXPIRED"
    INDETERMINATE = "INDETERMINATE"


class RealityGapType(str, Enum):
    """Descriptive relationship between expectation and observed reality."""

    NONE = "NONE"
    MISSING_EXPECTED_EVENT = "MISSING_EXPECTED_EVENT"
    UNEXPECTED_EVENT = "UNEXPECTED_EVENT"
    CONTRADICTORY_EVENT = "CONTRADICTORY_EVENT"
    BOTH = "BOTH"
    UNKNOWN = "UNKNOWN"


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{0} must be a string".format(field_name))
    normalized = value.strip()
    if not normalized:
        raise ValueError("{0} must not be empty".format(field_name))
    return normalized


def _positive_integer(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("{0} must be an integer".format(field_name))
    if value < 1:
        raise ValueError("{0} must be at least 1".format(field_name))
    return value


def _percentage(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{0} must be a real number".format(field_name))
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 100.0:
        raise ValueError("{0} must be between 0 and 100".format(field_name))
    return normalized


def _ratio(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{0} must be a real number".format(field_name))
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 <= normalized <= 1.0:
        raise ValueError("{0} must be between 0 and 1".format(field_name))
    return normalized


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


def _string_tuple(value: Any, field_name: str) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes, set, frozenset)):
        raise TypeError("{0} must be an ordered collection".format(field_name))
    try:
        items = tuple(_required_text(item, "{0} item".format(field_name)) for item in value)
    except TypeError as exc:
        raise TypeError("{0} must be an ordered collection".format(field_name)) from exc
    if len(set(items)) != len(items):
        raise ValueError("{0} must not contain duplicates".format(field_name))
    return items


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


def _deduplicate(values: Tuple[str, ...]) -> Tuple[str, ...]:
    result = []
    seen = set()
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return tuple(result)


@dataclass(frozen=True)
class ExpectationEvaluationPolicy:
    """Explicit Phase 1 coverage, surprise, and unexpected-event policy."""

    minimum_later_entries: int = 1
    sufficient_coverage_ratio: float = 0.60
    material_change_threshold: float = 20.0
    sharp_change_threshold: float = 35.0
    surprise_missing_weight: float = 50.0
    surprise_contradiction_weight: float = 70.0
    surprise_unexpected_weight: float = 20.0
    surprise_indeterminate_weight: float = 40.0
    strong_factor_threshold: float = 60.0
    high_horizon_threshold: float = 60.0
    policy_version: int = EVALUATION_POLICY_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "minimum_later_entries",
            _positive_integer(self.minimum_later_entries, "minimum_later_entries"),
        )
        object.__setattr__(
            self,
            "sufficient_coverage_ratio",
            _ratio(self.sufficient_coverage_ratio, "sufficient_coverage_ratio"),
        )
        for name in (
            "material_change_threshold",
            "sharp_change_threshold",
            "surprise_missing_weight",
            "surprise_contradiction_weight",
            "surprise_unexpected_weight",
            "surprise_indeterminate_weight",
            "strong_factor_threshold",
            "high_horizon_threshold",
        ):
            object.__setattr__(self, name, _percentage(getattr(self, name), name))
        object.__setattr__(
            self,
            "policy_version",
            _positive_integer(self.policy_version, "policy_version"),
        )
        if self.material_change_threshold > self.sharp_change_threshold:
            raise ValueError("material change must not exceed sharp change")


@dataclass(frozen=True)
class SituationExpectationEvaluation:
    """Immutable result of comparing a hypothesis with later Timeline facts."""

    evaluation_id: str
    expectation_id: str
    timeline_id: str
    source_timeline_version: int
    evaluated_timeline_version: int
    asset: str
    evaluated_at: datetime
    window_start: datetime
    window_end: datetime
    status: ExpectationEvaluationStatus
    gap_type: RealityGapType
    surprise_score: float
    observed_facts: Tuple[str, ...]
    fulfilled_criteria: Tuple[str, ...]
    missing_criteria: Tuple[str, ...]
    contradicted_criteria: Tuple[str, ...]
    unexpected_events: Tuple[str, ...]
    reason: str
    source_expectation_snapshot: TypingMapping[str, Any]
    evaluated_entry_ids: Tuple[str, ...]
    metadata: TypingMapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        for name in ("evaluation_id", "expectation_id", "timeline_id", "reason"):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))
        object.__setattr__(
            self,
            "source_timeline_version",
            _positive_integer(self.source_timeline_version, "source_timeline_version"),
        )
        object.__setattr__(
            self,
            "evaluated_timeline_version",
            _positive_integer(self.evaluated_timeline_version, "evaluated_timeline_version"),
        )
        if self.evaluated_timeline_version < self.source_timeline_version:
            raise ValueError("evaluated timeline version must not regress")
        object.__setattr__(self, "asset", _required_text(self.asset, "asset").upper())
        evaluated_at = _utc_datetime(self.evaluated_at, "evaluated_at")
        window_start = _utc_datetime(self.window_start, "window_start")
        window_end = _utc_datetime(self.window_end, "window_end")
        if window_end < window_start:
            raise ValueError("window_end must not precede window_start")
        object.__setattr__(self, "evaluated_at", evaluated_at)
        object.__setattr__(self, "window_start", window_start)
        object.__setattr__(self, "window_end", window_end)
        try:
            status = self.status if isinstance(self.status, ExpectationEvaluationStatus) else ExpectationEvaluationStatus(self.status)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid evaluation status") from exc
        object.__setattr__(self, "status", status)
        try:
            gap_type = self.gap_type if isinstance(self.gap_type, RealityGapType) else RealityGapType(self.gap_type)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid reality gap type") from exc
        object.__setattr__(self, "gap_type", gap_type)
        object.__setattr__(
            self,
            "surprise_score",
            _percentage(self.surprise_score, "surprise_score"),
        )
        for name in (
            "observed_facts",
            "fulfilled_criteria",
            "missing_criteria",
            "contradicted_criteria",
            "unexpected_events",
            "evaluated_entry_ids",
        ):
            object.__setattr__(self, name, _string_tuple(getattr(self, name), name))
        if not isinstance(self.source_expectation_snapshot, Mapping):
            raise TypeError("source_expectation_snapshot must be a mapping")
        object.__setattr__(
            self,
            "source_expectation_snapshot",
            _freeze(self.source_expectation_snapshot, "source_expectation_snapshot"),
        )
        object.__setattr__(self, "metadata", _freeze(self.metadata, "metadata"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "expectation_id": self.expectation_id,
            "timeline_id": self.timeline_id,
            "source_timeline_version": self.source_timeline_version,
            "evaluated_timeline_version": self.evaluated_timeline_version,
            "asset": self.asset,
            "evaluated_at": self.evaluated_at.isoformat(),
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "status": self.status.value,
            "gap_type": self.gap_type.value,
            "surprise_score": self.surprise_score,
            "observed_facts": list(self.observed_facts),
            "fulfilled_criteria": list(self.fulfilled_criteria),
            "missing_criteria": list(self.missing_criteria),
            "contradicted_criteria": list(self.contradicted_criteria),
            "unexpected_events": list(self.unexpected_events),
            "reason": self.reason,
            "source_expectation_snapshot": _plain(self.source_expectation_snapshot),
            "evaluated_entry_ids": list(self.evaluated_entry_ids),
            "metadata": _plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: TypingMapping[str, Any]) -> "SituationExpectationEvaluation":
        payload = _mapping_payload(data, "situation expectation evaluation")
        for name in ("evaluated_at", "window_start", "window_end"):
            payload[name] = _parse_datetime(payload.get(name), name)
        return cls(**payload)


def deterministic_evaluation_id(
    expectation: SituationExpectation,
    timeline: MarketSituationTimeline,
    evaluated_at: datetime,
) -> str:
    """Create a stable ID for one expectation/timeline/time comparison."""

    if not isinstance(expectation, SituationExpectation):
        raise TypeError("expectation must be a SituationExpectation")
    if not isinstance(timeline, MarketSituationTimeline):
        raise TypeError("timeline must be a MarketSituationTimeline")
    normalized = _utc_datetime(evaluated_at, "evaluated_at")
    return "evaluation:{0}:v{1}:{2}".format(
        expectation.expectation_id,
        timeline.version,
        normalized.strftime("%Y%m%dT%H%M%S%fZ"),
    )


@dataclass(frozen=True)
class _RuleEvaluation:
    fulfilled: bool = False
    contradicted: bool = False
    eligible_missing: bool = False
    unavailable: bool = False
    coverage_ratio: float = 0.0
    observed_facts: Tuple[str, ...] = ()
    fulfilled_criteria: Tuple[str, ...] = ()
    missing_criteria: Tuple[str, ...] = ()
    contradicted_criteria: Tuple[str, ...] = ()
    contradiction_severity: float = 0.0


class _ContractError(ValueError):
    pass


class SituationExpectationEvaluator:
    """Evaluate stored structured rules against later immutable Timeline entries."""

    def __init__(
        self,
        policy: Optional[ExpectationEvaluationPolicy] = None,
    ) -> None:
        if policy is not None and not isinstance(policy, ExpectationEvaluationPolicy):
            raise TypeError("policy must be an ExpectationEvaluationPolicy")
        self._policy = policy or ExpectationEvaluationPolicy()

    def evaluate(
        self,
        expectation: SituationExpectation,
        timeline: MarketSituationTimeline,
        *,
        evaluated_at: Optional[datetime] = None,
    ) -> SituationExpectationEvaluation:
        source_entry, evaluation_time = self._validate_inputs(
            expectation,
            timeline,
            evaluated_at,
        )
        evidence = self._evidence_entries(
            expectation,
            timeline,
            source_entry,
            evaluation_time,
        )
        window_closed = evaluation_time >= expectation.window_end
        before_window = evaluation_time < expectation.window_start
        contract_error = None
        rule_result = _RuleEvaluation()
        contract = expectation.metadata.get("evaluation_contract")

        if not before_window:
            try:
                validated_contract = self._validated_contract(expectation, contract)
                rule_result = self._evaluate_rule(
                    expectation,
                    source_entry,
                    evidence,
                    validated_contract,
                )
            except _ContractError as exc:
                contract_error = str(exc)

        unexpected_events = self._unexpected_events(
            expectation,
            source_entry,
            evidence,
            fulfilled=rule_result.fulfilled,
        )
        status, reason = self._status(
            before_window=before_window,
            window_closed=window_closed,
            evidence=evidence,
            result=rule_result,
            contract_error=contract_error,
        )
        fulfilled_criteria = (
            rule_result.fulfilled_criteria
            if status in (
                ExpectationEvaluationStatus.FULFILLED,
                ExpectationEvaluationStatus.INDETERMINATE,
            )
            else ()
        )
        contradicted_criteria = (
            rule_result.contradicted_criteria
            if status in (
                ExpectationEvaluationStatus.CONTRADICTED,
                ExpectationEvaluationStatus.INDETERMINATE,
            )
            else ()
        )
        missing_criteria = (
            rule_result.missing_criteria
            if status is ExpectationEvaluationStatus.MISSING
            else ()
        )
        gap_type = self._gap_type(status, unexpected_events)
        surprise_score = self._surprise_score(
            status,
            rule_result.coverage_ratio,
            rule_result.contradiction_severity,
            unexpected_events,
        )
        return SituationExpectationEvaluation(
            evaluation_id=deterministic_evaluation_id(
                expectation,
                timeline,
                evaluation_time,
            ),
            expectation_id=expectation.expectation_id,
            timeline_id=timeline.timeline_id,
            source_timeline_version=expectation.timeline_version,
            evaluated_timeline_version=timeline.version,
            asset=timeline.asset,
            evaluated_at=evaluation_time,
            window_start=expectation.window_start,
            window_end=expectation.window_end,
            status=status,
            gap_type=gap_type,
            surprise_score=surprise_score,
            observed_facts=_deduplicate(rule_result.observed_facts),
            fulfilled_criteria=_deduplicate(fulfilled_criteria),
            missing_criteria=_deduplicate(missing_criteria),
            contradicted_criteria=_deduplicate(contradicted_criteria),
            unexpected_events=unexpected_events,
            reason=reason,
            source_expectation_snapshot=expectation.to_dict(),
            evaluated_entry_ids=tuple(entry.entry_id for entry in evidence),
            metadata={
                "evaluation_policy_version": self._policy.policy_version,
                "evaluation_contract_version": (
                    contract.get("contract_version")
                    if isinstance(contract, Mapping)
                    else None
                ),
                "contract_error": contract_error,
                "coverage_ratio": rule_result.coverage_ratio,
                "evidence_entry_count": len(evidence),
                "evidence_cutoff": min(
                    evaluation_time,
                    expectation.window_end,
                ).isoformat(),
                "window_closed": window_closed,
                "post_window_evidence_ignored": any(
                    entry.created_at > expectation.window_end
                    and entry.created_at <= evaluation_time
                    for entry in timeline.entries
                ),
                "surprise_semantics": "departure_from_structured_expectation",
                "persistence": "none",
            },
        )

    @staticmethod
    def _validate_inputs(
        expectation: Any,
        timeline: Any,
        evaluated_at: Optional[datetime],
    ) -> Tuple[MarketSituationTimelineEntry, datetime]:
        if not isinstance(expectation, SituationExpectation):
            raise TypeError("expectation must be a SituationExpectation")
        if not isinstance(timeline, MarketSituationTimeline):
            raise TypeError("timeline must be a MarketSituationTimeline")
        if expectation.timeline_id != timeline.timeline_id:
            raise ValueError("expectation and Timeline IDs must match")
        if expectation.asset != timeline.asset:
            raise ValueError("expectation and Timeline assets must match")
        if timeline.version < expectation.timeline_version:
            raise ValueError("Timeline version must not precede expectation source version")
        source_entry = next(
            (
                entry
                for entry in timeline.entries
                if entry.entry_id == expectation.source_entry_id
            ),
            None,
        )
        if source_entry is None:
            raise ValueError("expectation source entry must remain in Timeline history")
        if source_entry.stage is not expectation.source_stage:
            raise ValueError("source entry stage no longer matches expectation snapshot")
        for name in FACTOR_FIELDS:
            if getattr(source_entry.dna, name) != expectation.source_factor_values[name]:
                raise ValueError("source factor values no longer match expectation snapshot")
            if source_entry.dna.factor_availability.get(name, "MISSING") != expectation.source_factor_availability[name]:
                raise ValueError("source factor availability no longer matches expectation snapshot")
        evaluation_time = (
            timeline.updated_at
            if evaluated_at is None
            else _utc_datetime(evaluated_at, "evaluated_at")
        )
        if evaluation_time < expectation.created_at:
            raise ValueError("evaluated_at must not precede expectation creation")
        return source_entry, evaluation_time

    @staticmethod
    def _evidence_entries(
        expectation: SituationExpectation,
        timeline: MarketSituationTimeline,
        source_entry: MarketSituationTimelineEntry,
        evaluated_at: datetime,
    ) -> Tuple[MarketSituationTimelineEntry, ...]:
        if evaluated_at < expectation.window_start:
            return ()
        cutoff = min(evaluated_at, expectation.window_end)
        return tuple(
            entry
            for entry in timeline.entries
            if entry.created_at > source_entry.created_at
            and entry.created_at >= expectation.window_start
            and entry.created_at <= cutoff
        )

    def _validated_contract(
        self,
        expectation: SituationExpectation,
        contract: Any,
    ) -> TypingMapping[str, Any]:
        if not isinstance(contract, Mapping):
            raise _ContractError("evaluation_contract is absent")
        required = (
            "contract_version",
            "rule_name",
            "expectation_kind",
            "subject",
            "source_policy_version",
            "source_timeline_version",
            "source_stage",
            "window_minutes",
        )
        missing = tuple(name for name in required if name not in contract)
        if missing:
            raise _ContractError(
                "evaluation_contract is incomplete: {0}".format(", ".join(missing))
            )
        if contract["contract_version"] != SUPPORTED_EVALUATION_CONTRACT_VERSION:
            raise _ContractError("evaluation_contract version is unsupported")
        if contract["expectation_kind"] != expectation.kind.value:
            raise _ContractError("evaluation_contract kind does not match expectation")
        if contract["subject"] != expectation.subject:
            raise _ContractError("evaluation_contract subject does not match expectation")
        if contract["source_timeline_version"] != expectation.timeline_version:
            raise _ContractError("evaluation_contract Timeline version does not match")
        if contract["source_stage"] != expectation.source_stage.value:
            raise _ContractError("evaluation_contract source stage does not match")
        actual_minutes = int(
            (expectation.window_end - expectation.window_start).total_seconds() / 60
        )
        if contract["window_minutes"] != actual_minutes:
            raise _ContractError("evaluation_contract window does not match expectation")
        rule_name = _contract_text(contract, "rule_name")
        self._validate_rule_contract(rule_name, contract)
        return contract

    @staticmethod
    def _validate_rule_contract(
        rule_name: str,
        contract: TypingMapping[str, Any],
    ) -> None:
        if rule_name == "volume_confirmation":
            _contract_text(contract, "target_factor")
            for name in (
                "confirmation_threshold",
                "structure_material_threshold",
                "structure_contradiction_threshold",
                "maturity_contradiction_threshold",
            ):
                _contract_percentage(contract, name)
            _contract_ratio(contract, "minimum_coverage_ratio")
        elif rule_name == "momentum_confirmation":
            _contract_text(contract, "target_factor")
            _contract_text_tuple(contract, "initiating_factors")
            for name in (
                "confirmation_threshold",
                "initiating_factor_threshold",
                "contradiction_threshold",
            ):
                _contract_percentage(contract, name)
            _contract_ratio(contract, "minimum_coverage_ratio")
        elif rule_name == "factor_persistence":
            _contract_text(contract, "target_factor")
            _contract_percentage(contract, "persistence_threshold")
            _contract_percentage(contract, "contradiction_threshold")
            _contract_positive_integer(contract, "minimum_required_later_entries")
        elif rule_name == "funding_appearance_after_structure_volume":
            _contract_text(contract, "target_factor")
            _contract_text(contract, "source_required_availability")
            _contract_text(contract, "fulfillment_availability")
            _contract_text(contract, "missing_confirmation_availability")
            _contract_text_tuple(contract, "disqualifying_availability_states")
            _contract_positive_integer(contract, "minimum_required_later_entries")
        elif rule_name.startswith("stage_advance_"):
            _contract_stage(contract, "source_stage")
            _contract_stage(contract, "expected_target_stage")
            _contract_stage_tuple(contract, "incompatible_stages")
            _contract_positive_integer(contract, "minimum_required_later_entries")
        elif rule_name.startswith("stage_persistence_"):
            _contract_stage(contract, "source_stage")
            _contract_stage(contract, "required_stage")
            _contract_positive_integer(contract, "minimum_required_later_entries")
        elif rule_name == "invalidation_risk":
            _contract_percentage(contract, "maturity_threshold")
            _contract_percentage(contract, "horizon_threshold")
            _contract_positive_integer(contract, "concentration_threshold")
            strengthening = _contract_mapping(contract, "strengthening_thresholds")
            weakening = _contract_mapping(contract, "weakening_thresholds")
            _contract_percentage(strengthening, "minimum_emergence_increase")
            _contract_percentage(strengthening, "minimum_horizon_increase")
            _contract_positive_integer(strengthening, "minimum_supporting_factor_count")
            _contract_percentage(weakening, "material_change_threshold")
            _contract_percentage(weakening, "sharp_change_threshold")
        else:
            raise _ContractError("evaluation_contract rule is unsupported")

    def _evaluate_rule(
        self,
        expectation: SituationExpectation,
        source_entry: MarketSituationTimelineEntry,
        evidence: Tuple[MarketSituationTimelineEntry, ...],
        contract: TypingMapping[str, Any],
    ) -> _RuleEvaluation:
        rule_name = contract["rule_name"]
        if rule_name == "volume_confirmation":
            return self._confirmation(evidence, contract, structure_rule=True)
        if rule_name == "momentum_confirmation":
            return self._confirmation(evidence, contract, structure_rule=False)
        if rule_name == "factor_persistence":
            return self._factor_persistence(evidence, contract)
        if rule_name == "funding_appearance_after_structure_volume":
            return self._factor_appearance(evidence, contract)
        if rule_name.startswith("stage_advance_"):
            return self._stage_advance(evidence, contract)
        if rule_name.startswith("stage_persistence_"):
            return self._stage_persistence(evidence, contract)
        if rule_name == "invalidation_risk":
            return self._invalidation_risk(source_entry, evidence, contract)
        raise _ContractError("evaluation_contract rule is unsupported")

    def _confirmation(
        self,
        evidence: Tuple[MarketSituationTimelineEntry, ...],
        contract: TypingMapping[str, Any],
        *,
        structure_rule: bool,
    ) -> _RuleEvaluation:
        target = contract["target_factor"]
        threshold = float(contract["confirmation_threshold"])
        minimum_coverage = float(contract["minimum_coverage_ratio"])
        measured = 0
        fulfilled = []
        contradicted = []
        facts = []
        severity = 0.0
        for entry in evidence:
            state = _availability(entry, target)
            value = getattr(entry.dna, target)
            facts.append(_factor_fact(entry, target, state, value))
            if state == "AVAILABLE" and value is not None:
                measured += 1
                if value >= threshold:
                    fulfilled.append(
                        "{0} reached {1:g}, meeting stored threshold {2:g}.".format(
                            target,
                            value,
                            threshold,
                        )
                    )
            if structure_rule:
                structure_state = _availability(entry, "structure_event")
                structure_value = entry.dna.structure_event
                contradiction_threshold = float(
                    contract["structure_contradiction_threshold"]
                )
                if (
                    structure_state == "AVAILABLE"
                    and structure_value is not None
                    and structure_value < contradiction_threshold
                ):
                    contradicted.append(
                        "Structure Event fell below stored contradiction threshold {0:g}.".format(
                            contradiction_threshold
                        )
                    )
                    severity = max(severity, contradiction_threshold - structure_value)
                maturity_threshold = float(
                    contract["maturity_contradiction_threshold"]
                )
                if (
                    entry.dna.maturity >= maturity_threshold
                    and state == "AVAILABLE"
                    and value is not None
                    and value < threshold
                ):
                    contradicted.append(
                        "Maturity reached {0:g} while {1} remained below {2:g}.".format(
                            entry.dna.maturity,
                            target,
                            threshold,
                        )
                    )
                    severity = max(severity, entry.dna.maturity - maturity_threshold)
            else:
                initiating = tuple(contract["initiating_factors"])
                contradiction_threshold = float(contract["contradiction_threshold"])
                if initiating and all(
                    _availability(entry, name) == "AVAILABLE"
                    and getattr(entry.dna, name) is not None
                    and getattr(entry.dna, name) < contradiction_threshold
                    for name in initiating
                ):
                    contradicted.append(
                        "All stored initiating factors fell below contradiction threshold {0:g}.".format(
                            contradiction_threshold
                        )
                    )
                    severity = max(
                        severity,
                        max(
                            contradiction_threshold - getattr(entry.dna, name)
                            for name in initiating
                        ),
                    )
        coverage = _coverage(measured, len(evidence))
        enough_entries = len(evidence) >= self._policy.minimum_later_entries
        eligible_missing = enough_entries and coverage >= minimum_coverage
        return _RuleEvaluation(
            fulfilled=bool(fulfilled),
            contradicted=bool(contradicted),
            eligible_missing=eligible_missing,
            unavailable=not eligible_missing,
            coverage_ratio=coverage,
            observed_facts=tuple(facts),
            fulfilled_criteria=tuple(fulfilled),
            missing_criteria=(
                "Expected {0} confirmation at or above {1:g} did not occur.".format(
                    target,
                    threshold,
                ),
            ),
            contradicted_criteria=tuple(contradicted),
            contradiction_severity=_bounded(severity),
        )

    @staticmethod
    def _factor_persistence(
        evidence: Tuple[MarketSituationTimelineEntry, ...],
        contract: TypingMapping[str, Any],
    ) -> _RuleEvaluation:
        target = contract["target_factor"]
        persistence_threshold = float(contract["persistence_threshold"])
        contradiction_threshold = float(contract["contradiction_threshold"])
        minimum_entries = int(contract["minimum_required_later_entries"])
        facts = []
        measured_entries = []
        contradicted = []
        severity = 0.0
        for entry in evidence:
            state = _availability(entry, target)
            value = getattr(entry.dna, target)
            facts.append(_factor_fact(entry, target, state, value))
            if state == "AVAILABLE" and value is not None:
                measured_entries.append((entry, value))
                if value < contradiction_threshold:
                    contradicted.append(
                        "{0} fell below stored persistence contradiction threshold {1:g}.".format(
                            target,
                            contradiction_threshold,
                        )
                    )
                    severity = max(severity, contradiction_threshold - value)
        latest_measured = measured_entries[-1] if measured_entries else None
        fulfilled = (
            len(evidence) >= minimum_entries
            and latest_measured is not None
            and latest_measured[0] is evidence[-1]
            and latest_measured[1] >= persistence_threshold
            and not contradicted
        )
        coverage = _coverage(len(measured_entries), len(evidence))
        sufficient = len(evidence) >= minimum_entries and coverage >= 1.0
        return _RuleEvaluation(
            fulfilled=fulfilled,
            contradicted=bool(contradicted),
            eligible_missing=sufficient and not fulfilled and not contradicted,
            unavailable=not sufficient,
            coverage_ratio=coverage,
            observed_facts=tuple(facts),
            fulfilled_criteria=(
                (
                    "{0} remained measured at or above stored persistence threshold {1:g}.".format(
                        target,
                        persistence_threshold,
                    )
                ),
            ) if fulfilled else (),
            missing_criteria=(
                "Expected measured {0} persistence did not occur.".format(target),
            ),
            contradicted_criteria=tuple(contradicted),
            contradiction_severity=_bounded(severity),
        )

    @staticmethod
    def _factor_appearance(
        evidence: Tuple[MarketSituationTimelineEntry, ...],
        contract: TypingMapping[str, Any],
    ) -> _RuleEvaluation:
        target = contract["target_factor"]
        fulfillment_state = contract["fulfillment_availability"]
        missing_state = contract["missing_confirmation_availability"]
        disqualifying = set(contract["disqualifying_availability_states"])
        minimum_entries = int(contract["minimum_required_later_entries"])
        states = tuple(_availability(entry, target) for entry in evidence)
        facts = tuple(
            _factor_fact(entry, target, state, getattr(entry.dna, target))
            for entry, state in zip(evidence, states)
        )
        fulfilled = fulfillment_state in states
        disqualified = any(state in disqualifying for state in states)
        adequate = sum(state in (fulfillment_state, missing_state) for state in states)
        coverage = _coverage(adequate, len(evidence))
        sufficient = (
            len(evidence) >= minimum_entries
            and adequate >= minimum_entries
            and coverage >= 1.0
        )
        return _RuleEvaluation(
            fulfilled=fulfilled,
            contradicted=False,
            eligible_missing=sufficient and not fulfilled and not disqualified,
            unavailable=disqualified or not sufficient,
            coverage_ratio=coverage,
            observed_facts=facts,
            fulfilled_criteria=(
                "{0} changed from stored MISSING source state to AVAILABLE.".format(target),
            ) if fulfilled else (),
            missing_criteria=(
                "Expected {0} appearance did not occur; later observations remained explicitly MISSING.".format(
                    target
                ),
            ),
        )

    @staticmethod
    def _stage_advance(
        evidence: Tuple[MarketSituationTimelineEntry, ...],
        contract: TypingMapping[str, Any],
    ) -> _RuleEvaluation:
        target = EmergingStage(contract["expected_target_stage"])
        incompatible = {EmergingStage(value) for value in contract["incompatible_stages"]}
        minimum_entries = int(contract["minimum_required_later_entries"])
        fulfilled_entries = tuple(entry for entry in evidence if entry.stage is target)
        contradicted_entries = tuple(entry for entry in evidence if entry.stage in incompatible)
        facts = tuple(
            "{0}: stage={1}.".format(entry.entry_id, entry.stage.value)
            for entry in evidence
        )
        return _RuleEvaluation(
            fulfilled=bool(fulfilled_entries),
            contradicted=bool(contradicted_entries),
            eligible_missing=(
                len(evidence) >= minimum_entries
                and not fulfilled_entries
                and not contradicted_entries
            ),
            unavailable=len(evidence) < minimum_entries,
            coverage_ratio=1.0 if evidence else 0.0,
            observed_facts=facts,
            fulfilled_criteria=(
                "Exact expected next stage {0} was recorded within the window.".format(
                    target.value
                ),
            ) if fulfilled_entries else (),
            missing_criteria=(
                "Expected next stage {0} was not recorded within the window.".format(
                    target.value
                ),
            ),
            contradicted_criteria=tuple(
                "Incompatible stage {0} was recorded instead of exact next stage {1}.".format(
                    entry.stage.value,
                    target.value,
                )
                for entry in contradicted_entries
            ),
            contradiction_severity=(100.0 if contradicted_entries else 0.0),
        )

    @staticmethod
    def _stage_persistence(
        evidence: Tuple[MarketSituationTimelineEntry, ...],
        contract: TypingMapping[str, Any],
    ) -> _RuleEvaluation:
        required = EmergingStage(contract["required_stage"])
        minimum_entries = int(contract["minimum_required_later_entries"])
        changed = tuple(entry for entry in evidence if entry.stage is not required)
        sufficient = len(evidence) >= minimum_entries
        fulfilled = sufficient and not changed
        facts = tuple(
            "{0}: stage={1}.".format(entry.entry_id, entry.stage.value)
            for entry in evidence
        )
        return _RuleEvaluation(
            fulfilled=fulfilled,
            contradicted=bool(changed),
            eligible_missing=False,
            unavailable=not sufficient,
            coverage_ratio=1.0 if evidence else 0.0,
            observed_facts=facts,
            fulfilled_criteria=(
                "Required stage {0} persisted through later measured entries.".format(
                    required.value
                ),
            ) if fulfilled else (),
            contradicted_criteria=tuple(
                "Stage changed from required {0} to {1}.".format(
                    required.value,
                    entry.stage.value,
                )
                for entry in changed
            ),
            contradiction_severity=(100.0 if changed else 0.0),
        )

    @staticmethod
    def _invalidation_risk(
        source_entry: MarketSituationTimelineEntry,
        evidence: Tuple[MarketSituationTimelineEntry, ...],
        contract: TypingMapping[str, Any],
    ) -> _RuleEvaluation:
        maturity_threshold = float(contract["maturity_threshold"])
        horizon_threshold = float(contract["horizon_threshold"])
        concentration_threshold = int(contract["concentration_threshold"])
        strengthening = contract["strengthening_thresholds"]
        emergence_increase = float(strengthening["minimum_emergence_increase"])
        horizon_increase = float(strengthening["minimum_horizon_increase"])
        support_minimum = int(strengthening["minimum_supporting_factor_count"])
        source_support_count = len(set(source_entry.supporting_factors))
        fulfilled = []
        contradicted = []
        facts = []
        severity = 0.0
        for entry in evidence:
            support_count = len(set(entry.supporting_factors))
            facts.append(
                "{0}: stage={1}, maturity={2:g}, horizon={3:g}, supporting_factors={4}.".format(
                    entry.entry_id,
                    entry.stage.value,
                    entry.dna.maturity,
                    entry.dna.horizon,
                    support_count,
                )
            )
            invalidated = False
            if entry.stage is EmergingStage.EXHAUSTED:
                fulfilled.append("Stage became EXHAUSTED within the window.")
                severity = max(severity, 100.0)
                invalidated = True
            if (
                entry.dna.maturity >= maturity_threshold
                and entry.dna.horizon <= horizon_threshold
            ):
                fulfilled.append(
                    "Maturity reached {0:g} while Horizon fell to {1:g}.".format(
                        entry.dna.maturity,
                        entry.dna.horizon,
                    )
                )
                severity = max(
                    severity,
                    entry.dna.maturity - maturity_threshold,
                    horizon_threshold - entry.dna.horizon,
                )
                invalidated = True
            if (
                source_support_count > concentration_threshold
                and support_count <= concentration_threshold
            ):
                fulfilled.append(
                    "Measured supporting-factor count contracted to {0}.".format(
                        support_count
                    )
                )
                severity = max(severity, 50.0)
                invalidated = True
            strengthened = (
                entry.dna.emergence - source_entry.dna.emergence >= emergence_increase
                and entry.dna.horizon - source_entry.dna.horizon >= horizon_increase
                and support_count >= support_minimum
            )
            if strengthened and not invalidated:
                contradicted.append(
                    "Situation strengthened beyond stored emergence, horizon, and support thresholds."
                )
                severity = max(
                    severity,
                    entry.dna.emergence - source_entry.dna.emergence,
                    entry.dna.horizon - source_entry.dna.horizon,
                )
        sufficient = len(evidence) >= 1
        return _RuleEvaluation(
            fulfilled=bool(fulfilled),
            contradicted=bool(contradicted),
            eligible_missing=sufficient and not fulfilled and not contradicted,
            unavailable=not sufficient,
            coverage_ratio=1.0 if evidence else 0.0,
            observed_facts=tuple(facts),
            fulfilled_criteria=tuple(fulfilled),
            missing_criteria=(
                "Stored invalidation-risk conditions did not occur within the window.",
            ),
            contradicted_criteria=tuple(contradicted),
            contradiction_severity=_bounded(severity),
        )

    def _unexpected_events(
        self,
        expectation: SituationExpectation,
        source_entry: MarketSituationTimelineEntry,
        evidence: Tuple[MarketSituationTimelineEntry, ...],
        *,
        fulfilled: bool,
    ) -> Tuple[str, ...]:
        events = []
        appearance_subject = (
            expectation.subject
            if expectation.kind is ExpectationKind.FACTOR_APPEARANCE
            else None
        )
        for name in FACTOR_FIELDS:
            if (
                name != appearance_subject
                and expectation.source_factor_availability[name] == "MISSING"
                and any(_availability(entry, name) == "AVAILABLE" for entry in evidence)
            ):
                events.append(
                    "Previously MISSING factor {0} became AVAILABLE outside this expectation subject.".format(
                        name
                    )
                )
        for entry in evidence:
            stage_distance = abs(
                _STAGE_INDEX[entry.stage] - _STAGE_INDEX[source_entry.stage]
            )
            if stage_distance > 1:
                events.append(
                    "Stage changed by more than one lifecycle step: {0} to {1}.".format(
                        source_entry.stage.value,
                        entry.stage.value,
                    )
                )
            for name in INITIATING_FACTORS:
                source_value = expectation.source_factor_values[name]
                if (
                    source_value is not None
                    and source_value >= self._policy.strong_factor_threshold
                    and _availability(entry, name) != "AVAILABLE"
                ):
                    events.append(
                        "Strong source factor {0} became unavailable.".format(name)
                    )
            if (
                source_entry.dna.emergence - entry.dna.emergence
                >= self._policy.material_change_threshold
                and entry.dna.horizon >= self._policy.high_horizon_threshold
            ):
                events.append(
                    "Emergence collapsed materially while Horizon remained high."
                )
            if (
                not fulfilled
                and entry.dna.maturity - source_entry.dna.maturity
                >= self._policy.sharp_change_threshold
            ):
                events.append(
                    "Maturity rose sharply without stored expectation fulfillment."
                )
        return tuple(sorted(set(events)))

    @staticmethod
    def _status(
        *,
        before_window: bool,
        window_closed: bool,
        evidence: Tuple[MarketSituationTimelineEntry, ...],
        result: _RuleEvaluation,
        contract_error: Optional[str],
    ) -> Tuple[ExpectationEvaluationStatus, str]:
        if before_window:
            return (
                ExpectationEvaluationStatus.PENDING,
                "The evaluation window has not started.",
            )
        if contract_error is not None:
            if not window_closed:
                return (
                    ExpectationEvaluationStatus.PENDING,
                    "The window is open; structured evaluation metadata is unavailable.",
                )
            if evidence:
                return (
                    ExpectationEvaluationStatus.INDETERMINATE,
                    "Later evidence exists, but the historical evaluation contract is absent or incomplete.",
                )
            return (
                ExpectationEvaluationStatus.EXPIRED,
                "The window ended without evidence or an authoritative evaluation contract.",
            )
        if result.fulfilled and result.contradicted:
            return (
                ExpectationEvaluationStatus.INDETERMINATE,
                "Fulfillment and contradiction were both materially supported within the window.",
            )
        if result.contradicted:
            return (
                ExpectationEvaluationStatus.CONTRADICTED,
                "Measured evidence satisfied the stored contradiction contract.",
            )
        if result.fulfilled:
            return (
                ExpectationEvaluationStatus.FULFILLED,
                "Measured evidence satisfied the stored fulfillment contract.",
            )
        if not window_closed:
            return (
                ExpectationEvaluationStatus.PENDING,
                "The evaluation window remains open without a conclusive result.",
            )
        if result.eligible_missing:
            return (
                ExpectationEvaluationStatus.MISSING,
                "The window ended with sufficient measured coverage and the expected event did not occur.",
            )
        return (
            ExpectationEvaluationStatus.EXPIRED,
            "The window ended without sufficient measured evidence for a missing-event conclusion.",
        )

    @staticmethod
    def _gap_type(
        status: ExpectationEvaluationStatus,
        unexpected_events: Tuple[str, ...],
    ) -> RealityGapType:
        has_unexpected = bool(unexpected_events)
        if status is ExpectationEvaluationStatus.FULFILLED:
            return RealityGapType.UNEXPECTED_EVENT if has_unexpected else RealityGapType.NONE
        if status is ExpectationEvaluationStatus.MISSING:
            return RealityGapType.BOTH if has_unexpected else RealityGapType.MISSING_EXPECTED_EVENT
        if status is ExpectationEvaluationStatus.CONTRADICTED:
            return RealityGapType.BOTH if has_unexpected else RealityGapType.CONTRADICTORY_EVENT
        if status is ExpectationEvaluationStatus.PENDING:
            return RealityGapType.UNEXPECTED_EVENT if has_unexpected else RealityGapType.NONE
        if status is ExpectationEvaluationStatus.INDETERMINATE and has_unexpected:
            return RealityGapType.BOTH
        return RealityGapType.UNKNOWN

    def _surprise_score(
        self,
        status: ExpectationEvaluationStatus,
        coverage_ratio: float,
        contradiction_severity: float,
        unexpected_events: Tuple[str, ...],
    ) -> float:
        if status is ExpectationEvaluationStatus.PENDING:
            return 0.0
        unexpected = min(
            self._policy.surprise_unexpected_weight,
            len(unexpected_events) * self._policy.surprise_unexpected_weight / 2.0,
        )
        if status is ExpectationEvaluationStatus.FULFILLED:
            base = 0.0
        elif status is ExpectationEvaluationStatus.MISSING:
            base = self._policy.surprise_missing_weight + 20.0 * (
                1.0 - max(0.0, min(1.0, coverage_ratio))
            )
        elif status is ExpectationEvaluationStatus.CONTRADICTED:
            base = self._policy.surprise_contradiction_weight + 0.20 * contradiction_severity
        elif status is ExpectationEvaluationStatus.EXPIRED:
            base = 25.0
        else:
            base = self._policy.surprise_indeterminate_weight + 0.20 * max(
                contradiction_severity,
                50.0,
            )
        return round(min(100.0, base + unexpected), 6)


def _bounded(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 6)


def _coverage(adequate: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(float(adequate) / float(total), 6)


def _availability(entry: MarketSituationTimelineEntry, factor_name: str) -> str:
    return entry.dna.factor_availability.get(factor_name, "MISSING")


def _factor_fact(
    entry: MarketSituationTimelineEntry,
    factor_name: str,
    availability: str,
    value: Optional[float],
) -> str:
    rendered = "None" if value is None else "{0:g}".format(value)
    return "{0}: {1}={2} {3}.".format(
        entry.entry_id,
        factor_name,
        rendered,
        availability,
    )


def _contract_mapping(contract: TypingMapping[str, Any], name: str) -> TypingMapping[str, Any]:
    value = contract.get(name)
    if not isinstance(value, Mapping):
        raise _ContractError("evaluation_contract field {0} must be a mapping".format(name))
    return value


def _contract_text(contract: TypingMapping[str, Any], name: str) -> str:
    try:
        return _required_text(contract.get(name), "evaluation_contract {0}".format(name))
    except (TypeError, ValueError) as exc:
        raise _ContractError(str(exc)) from exc


def _contract_percentage(contract: TypingMapping[str, Any], name: str) -> float:
    try:
        return _percentage(contract.get(name), "evaluation_contract {0}".format(name))
    except (TypeError, ValueError) as exc:
        raise _ContractError(str(exc)) from exc


def _contract_ratio(contract: TypingMapping[str, Any], name: str) -> float:
    try:
        return _ratio(contract.get(name), "evaluation_contract {0}".format(name))
    except (TypeError, ValueError) as exc:
        raise _ContractError(str(exc)) from exc


def _contract_positive_integer(contract: TypingMapping[str, Any], name: str) -> int:
    try:
        return _positive_integer(contract.get(name), "evaluation_contract {0}".format(name))
    except (TypeError, ValueError) as exc:
        raise _ContractError(str(exc)) from exc


def _contract_text_tuple(contract: TypingMapping[str, Any], name: str) -> Tuple[str, ...]:
    value = contract.get(name)
    try:
        items = _string_tuple(value, "evaluation_contract {0}".format(name))
    except (TypeError, ValueError) as exc:
        raise _ContractError(str(exc)) from exc
    if not items:
        raise _ContractError("evaluation_contract {0} must not be empty".format(name))
    return items


def _contract_stage(contract: TypingMapping[str, Any], name: str) -> EmergingStage:
    try:
        return EmergingStage(contract.get(name))
    except (TypeError, ValueError) as exc:
        raise _ContractError("evaluation_contract {0} must be a stage".format(name)) from exc


def _contract_stage_tuple(contract: TypingMapping[str, Any], name: str) -> Tuple[EmergingStage, ...]:
    values = _contract_text_tuple(contract, name)
    try:
        return tuple(EmergingStage(value) for value in values)
    except ValueError as exc:
        raise _ContractError("evaluation_contract {0} contains invalid stage".format(name)) from exc


def _expectation_label(snapshot: TypingMapping[str, Any]) -> str:
    subject = snapshot.get("subject", "expectation")
    return str(subject).replace("_", " ").title()


def format_expectation_evaluation(
    evaluation: SituationExpectationEvaluation,
) -> str:
    """Render an immutable evaluation without Telegram markup or trade advice."""

    if not isinstance(evaluation, SituationExpectationEvaluation):
        raise TypeError("evaluation must be a SituationExpectationEvaluation")
    lines = [
        evaluation.asset,
        "",
        "Expectation:",
        _expectation_label(evaluation.source_expectation_snapshot),
        "",
        "Status:",
        evaluation.status.value,
        "",
        "Window:",
        "{0}-{1} UTC".format(
            evaluation.window_start.strftime("%H:%M"),
            evaluation.window_end.strftime("%H:%M"),
        ),
        "",
        "Observed:",
    ]
    lines.extend(
        "- {0}".format(item)
        for item in (evaluation.observed_facts or ("No conclusive measured facts.",))
    )
    lines.extend(["", "What did not happen that should have happened?"])
    lines.extend(
        "- {0}".format(item)
        for item in (evaluation.missing_criteria or ("None established.",))
    )
    lines.extend(["", "What happened that should not have happened?"])
    reality_gaps = evaluation.contradicted_criteria + evaluation.unexpected_events
    lines.extend(
        "- {0}".format(item)
        for item in (reality_gaps or ("None established.",))
    )
    lines.extend(["", "Surprise:", "{0:g}".format(evaluation.surprise_score)])
    return "\n".join(lines)


def format_expectation_evaluations(
    evaluations: Tuple[SituationExpectationEvaluation, ...],
) -> str:
    """Render a deterministic collection of expectation evaluations."""

    if isinstance(evaluations, (str, bytes, set, frozenset)):
        raise TypeError("evaluations must be an ordered collection")
    values = tuple(evaluations)
    if not all(isinstance(item, SituationExpectationEvaluation) for item in values):
        raise TypeError("evaluations must contain SituationExpectationEvaluation objects")
    if not values:
        return "No expectation evaluations."
    return "\n\n".join(format_expectation_evaluation(item) for item in values)


__all__ = [
    "ExpectationEvaluationPolicy",
    "ExpectationEvaluationStatus",
    "RealityGapType",
    "SituationExpectationEvaluation",
    "SituationExpectationEvaluator",
    "deterministic_evaluation_id",
    "format_expectation_evaluation",
    "format_expectation_evaluations",
]
