"""Deterministic pre-window hypotheses for Market Situation timelines."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
import math
from numbers import Real
from types import MappingProxyType
from typing import Any, Callable, Dict, Mapping as TypingMapping, Optional, Tuple

from app.intelligence.early_bird import EmergingStage
from app.intelligence.timeline.models import MarketSituationTimeline, SituationDNA


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

AVAILABLE = "AVAILABLE"
MISSING = "MISSING"
EVALUATION_CONTRACT_VERSION = "1"
EVALUATION_MINIMUM_COVERAGE_RATIO = 0.60
EVALUATION_MATERIAL_CHANGE_THRESHOLD = 20.0
EVALUATION_SHARP_CHANGE_THRESHOLD = 35.0


class ExpectationKind(str, Enum):
    """Descriptive classification of a future measurable hypothesis."""

    FACTOR_INCREASE = "FACTOR_INCREASE"
    FACTOR_DECREASE = "FACTOR_DECREASE"
    FACTOR_APPEARANCE = "FACTOR_APPEARANCE"
    FACTOR_PERSISTENCE = "FACTOR_PERSISTENCE"
    STAGE_ADVANCE = "STAGE_ADVANCE"
    STAGE_PERSISTENCE = "STAGE_PERSISTENCE"
    CONFIRMATION = "CONFIRMATION"
    INVALIDATION_RISK = "INVALIDATION_RISK"


class ExpectationStrength(str, Enum):
    """Descriptive evidence strength, not market or trade confidence."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


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


def _optional_percentage(value: Any, field_name: str) -> Optional[float]:
    if value is None:
        return None
    return _percentage(value, field_name)


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
    if not items:
        raise ValueError("{0} must not be empty".format(field_name))
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


def _factor_values(value: Any) -> TypingMapping[str, Optional[float]]:
    if not isinstance(value, Mapping):
        raise TypeError("source_factor_values must be a mapping")
    if set(value) != set(FACTOR_FIELDS):
        raise ValueError("source_factor_values must contain all approved factors")
    return MappingProxyType({
        name: _optional_percentage(value[name], "source factor {0}".format(name))
        for name in FACTOR_FIELDS
    })


def _factor_availability(value: Any) -> TypingMapping[str, str]:
    if not isinstance(value, Mapping):
        raise TypeError("source_factor_availability must be a mapping")
    if set(value) != set(FACTOR_FIELDS):
        raise ValueError("source_factor_availability must contain all approved factors")
    return MappingProxyType({
        name: _required_text(value[name], "factor availability {0}".format(name)).upper()
        for name in FACTOR_FIELDS
    })


@dataclass(frozen=True)
class ExpectationPolicy:
    """Explicit Phase 1 thresholds and windows for hypothesis generation."""

    default_window_minutes: int = 60
    short_window_minutes: int = 30
    long_window_minutes: int = 120
    material_factor_threshold: float = 25.0
    strong_factor_threshold: float = 60.0
    weak_confirmation_threshold: float = 35.0
    high_maturity_threshold: float = 70.0
    low_horizon_threshold: float = 30.0
    minimum_detection_confidence: float = 40.0
    maximum_expectations: int = 5
    policy_version: int = 1

    def __post_init__(self) -> None:
        for name in (
            "default_window_minutes",
            "short_window_minutes",
            "long_window_minutes",
            "maximum_expectations",
            "policy_version",
        ):
            object.__setattr__(self, name, _positive_integer(getattr(self, name), name))
        for name in (
            "material_factor_threshold",
            "strong_factor_threshold",
            "weak_confirmation_threshold",
            "high_maturity_threshold",
            "low_horizon_threshold",
            "minimum_detection_confidence",
        ):
            object.__setattr__(self, name, _percentage(getattr(self, name), name))
        if not self.short_window_minutes <= self.default_window_minutes <= self.long_window_minutes:
            raise ValueError("windows must be ordered short <= default <= long")
        if self.material_factor_threshold > self.strong_factor_threshold:
            raise ValueError("material threshold must not exceed strong threshold")


@dataclass(frozen=True)
class SituationExpectation:
    """Immutable hypothesis captured before its evaluation window closes."""

    expectation_id: str
    timeline_id: str
    timeline_version: int
    asset: str
    created_at: datetime
    window_start: datetime
    window_end: datetime
    kind: ExpectationKind
    strength: ExpectationStrength
    subject: str
    description: str
    basis: Tuple[str, ...]
    fulfillment_criteria: Tuple[str, ...]
    contradiction_criteria: Tuple[str, ...]
    source_entry_id: str
    source_stage: EmergingStage
    source_factor_values: TypingMapping[str, Optional[float]]
    source_factor_availability: TypingMapping[str, str]
    metadata: TypingMapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        for name in ("expectation_id", "timeline_id", "subject", "description", "source_entry_id"):
            object.__setattr__(self, name, _required_text(getattr(self, name), name))
        object.__setattr__(self, "timeline_version", _positive_integer(self.timeline_version, "timeline_version"))
        object.__setattr__(self, "asset", _required_text(self.asset, "asset").upper())
        created_at = _utc_datetime(self.created_at, "created_at")
        window_start = _utc_datetime(self.window_start, "window_start")
        window_end = _utc_datetime(self.window_end, "window_end")
        if not created_at <= window_start <= window_end:
            raise ValueError("timestamps must satisfy created_at <= window_start <= window_end")
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "window_start", window_start)
        object.__setattr__(self, "window_end", window_end)
        try:
            kind = self.kind if isinstance(self.kind, ExpectationKind) else ExpectationKind(self.kind)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid expectation kind") from exc
        object.__setattr__(self, "kind", kind)
        try:
            strength = self.strength if isinstance(self.strength, ExpectationStrength) else ExpectationStrength(self.strength)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid expectation strength") from exc
        object.__setattr__(self, "strength", strength)
        for name in ("basis", "fulfillment_criteria", "contradiction_criteria"):
            object.__setattr__(self, name, _string_tuple(getattr(self, name), name))
        stage = self.source_stage
        if not isinstance(stage, EmergingStage):
            try:
                stage = EmergingStage(stage)
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid source_stage") from exc
        object.__setattr__(self, "source_stage", stage)
        values = _factor_values(self.source_factor_values)
        availability = _factor_availability(self.source_factor_availability)
        for name in FACTOR_FIELDS:
            if availability[name] == AVAILABLE and values[name] is None:
                raise ValueError("AVAILABLE source factor must have a measured value")
            if availability[name] != AVAILABLE and values[name] is not None:
                raise ValueError("non-AVAILABLE source factor must not have a measured value")
        object.__setattr__(self, "source_factor_values", values)
        object.__setattr__(self, "source_factor_availability", availability)
        object.__setattr__(self, "metadata", _freeze(self.metadata, "metadata"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expectation_id": self.expectation_id,
            "timeline_id": self.timeline_id,
            "timeline_version": self.timeline_version,
            "asset": self.asset,
            "created_at": self.created_at.isoformat(),
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "kind": self.kind.value,
            "strength": self.strength.value,
            "subject": self.subject,
            "description": self.description,
            "basis": list(self.basis),
            "fulfillment_criteria": list(self.fulfillment_criteria),
            "contradiction_criteria": list(self.contradiction_criteria),
            "source_entry_id": self.source_entry_id,
            "source_stage": self.source_stage.value,
            "source_factor_values": dict(self.source_factor_values),
            "source_factor_availability": dict(self.source_factor_availability),
            "metadata": _plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: TypingMapping[str, Any]) -> "SituationExpectation":
        payload = _mapping_payload(data, "situation expectation")
        for name in ("created_at", "window_start", "window_end"):
            payload[name] = _parse_datetime(payload.get(name), name)
        return cls(**payload)


ExpectationIdFactory = Callable[[MarketSituationTimeline, str, str], str]


def deterministic_expectation_id(
    timeline: MarketSituationTimeline,
    rule_name: str,
    subject: str,
) -> str:
    """Derive a stable ID from the exact timeline version and rule identity."""

    if not isinstance(timeline, MarketSituationTimeline):
        raise TypeError("timeline must be a MarketSituationTimeline")
    return "expectation:{0}:v{1}:{2}:{3}".format(
        timeline.timeline_id,
        timeline.version,
        _required_text(rule_name, "rule_name").lower(),
        _required_text(subject, "subject").lower(),
    )


@dataclass(frozen=True)
class _RuleOutput:
    order: int
    rule_name: str
    kind: ExpectationKind
    strength: ExpectationStrength
    subject: str
    description: str
    basis: Tuple[str, ...]
    fulfillment: Tuple[str, ...]
    contradiction: Tuple[str, ...]
    window_minutes: int
    evaluation_parameters: TypingMapping[str, Any]


class SituationExpectationEngine:
    """Generate hypotheses from the latest immutable Timeline entry only."""

    def __init__(
        self,
        policy: Optional[ExpectationPolicy] = None,
        id_factory: Optional[ExpectationIdFactory] = None,
    ) -> None:
        if policy is not None and not isinstance(policy, ExpectationPolicy):
            raise TypeError("policy must be an ExpectationPolicy")
        if id_factory is not None and not callable(id_factory):
            raise TypeError("id_factory must be callable")
        self._policy = policy or ExpectationPolicy()
        self._id_factory = id_factory or deterministic_expectation_id

    def generate(
        self,
        timeline: MarketSituationTimeline,
        *,
        created_at: Optional[datetime] = None,
    ) -> Tuple[SituationExpectation, ...]:
        if not isinstance(timeline, MarketSituationTimeline):
            raise TypeError("timeline must be a MarketSituationTimeline")
        if not timeline.entries:
            raise ValueError("timeline must contain at least one entry")
        entry = timeline.entries[-1]
        generated_at = timeline.updated_at if created_at is None else _utc_datetime(created_at, "created_at")
        if generated_at < entry.created_at:
            raise ValueError("created_at must not precede the latest Timeline entry")
        values = {name: getattr(entry.dna, name) for name in FACTOR_FIELDS}
        availability = {name: entry.dna.factor_availability.get(name, "MISSING") for name in FACTOR_FIELDS}
        rules = []
        rules.extend(self._volume_confirmation(entry.dna, availability))
        rules.extend(self._momentum_confirmation(entry.dna, availability))
        rules.extend(self._factor_persistence(entry.dna, availability))
        rules.extend(self._factor_appearance(entry.dna, availability))
        advance = self._stage_advance(entry.stage, entry.dna, availability, entry.supporting_factors)
        rules.extend(advance)
        rules.extend(self._stage_persistence(entry.stage, entry.dna, availability, entry.supporting_factors, bool(advance)))
        rules.extend(self._invalidation_risk(entry.stage, entry.dna, availability, entry.supporting_factors))
        identified_rules = tuple(
            (
                output,
                _required_text(
                    self._id_factory(timeline, output.rule_name, output.subject),
                    "expectation_id",
                ),
            )
            for output in rules
        )
        identified_rules = tuple(sorted(
            identified_rules,
            key=lambda item: (item[0].order, item[0].subject, item[1]),
        ))
        expectations = []
        ids = set()
        for output, expectation_id in identified_rules[: self._policy.maximum_expectations]:
            if expectation_id in ids:
                raise ValueError("expectation ID factory produced a duplicate")
            ids.add(expectation_id)
            expectations.append(
                SituationExpectation(
                    expectation_id=expectation_id,
                    timeline_id=timeline.timeline_id,
                    timeline_version=timeline.version,
                    asset=timeline.asset,
                    created_at=generated_at,
                    window_start=generated_at,
                    window_end=generated_at + timedelta(minutes=output.window_minutes),
                    kind=output.kind,
                    strength=output.strength,
                    subject=output.subject,
                    description=output.description,
                    basis=output.basis,
                    fulfillment_criteria=output.fulfillment,
                    contradiction_criteria=output.contradiction,
                    source_entry_id=entry.entry_id,
                    source_stage=entry.stage,
                    source_factor_values=values,
                    source_factor_availability=availability,
                    metadata={
                        "policy_version": self._policy.policy_version,
                        "rule_name": output.rule_name,
                        "window_minutes": output.window_minutes,
                        "source_entry_created_at": entry.created_at.isoformat(),
                        "generation_semantics": "hypothesis_not_evaluation",
                        "evaluation_contract": self._evaluation_contract(
                            timeline,
                            entry,
                            output,
                        ),
                    },
                )
            )
        return tuple(expectations)

    def _evaluation_contract(
        self,
        timeline: MarketSituationTimeline,
        entry: Any,
        output: _RuleOutput,
    ) -> TypingMapping[str, Any]:
        contract = {
            "contract_version": EVALUATION_CONTRACT_VERSION,
            "rule_name": output.rule_name,
            "expectation_kind": output.kind.value,
            "subject": output.subject,
            "source_policy_version": self._policy.policy_version,
            "source_timeline_version": timeline.version,
            "source_stage": entry.stage.value,
            "window_minutes": output.window_minutes,
        }
        contract.update(dict(output.evaluation_parameters))
        return contract

    def _available(self, dna: SituationDNA, availability: TypingMapping[str, str], name: str) -> bool:
        return availability.get(name) == AVAILABLE and getattr(dna, name) is not None

    def _basis_factor(self, dna: SituationDNA, name: str) -> str:
        return "{0}={1} AVAILABLE".format(name, _number(getattr(dna, name)))

    def _volume_confirmation(self, dna: SituationDNA, availability: TypingMapping[str, str]) -> Tuple[_RuleOutput, ...]:
        policy = self._policy
        if not (
            self._available(dna, availability, "structure_event")
            and dna.structure_event >= policy.material_factor_threshold
            and self._available(dna, availability, "volume_expansion")
            and dna.volume_expansion < policy.weak_confirmation_threshold
            and dna.detection_confidence >= policy.minimum_detection_confidence
        ):
            return ()
        return (_RuleOutput(
            1,
            "volume_confirmation",
            ExpectationKind.CONFIRMATION,
            ExpectationStrength.MEDIUM,
            "volume_expansion",
            "Measured structure activity is present; future measured volume confirmation is expected within the evaluation window.",
            (
                self._basis_factor(dna, "structure_event"),
                self._basis_factor(dna, "volume_expansion"),
                "detection_confidence={0}".format(_number(dna.detection_confidence)),
            ),
            ("Volume Expansion should rise to at least {0} while measured within the window.".format(_number(policy.weak_confirmation_threshold)),),
            (
                "The window expires without measured Volume Expansion confirmation.",
                "Measured Structure Event falls below {0}.".format(_number(policy.material_factor_threshold)),
                "Maturity increases while measured Volume Expansion remains below confirmation.",
            ),
            policy.default_window_minutes,
            {
                "target_factor": "volume_expansion",
                "confirmation_threshold": policy.weak_confirmation_threshold,
                "structure_material_threshold": policy.material_factor_threshold,
                "structure_contradiction_threshold": policy.material_factor_threshold,
                "maturity_contradiction_threshold": min(
                    100.0,
                    dna.maturity + EVALUATION_MATERIAL_CHANGE_THRESHOLD,
                ),
                "minimum_coverage_ratio": EVALUATION_MINIMUM_COVERAGE_RATIO,
            },
        ),)

    def _momentum_confirmation(self, dna: SituationDNA, availability: TypingMapping[str, str]) -> Tuple[_RuleOutput, ...]:
        policy = self._policy
        initiating = tuple(
            name
            for name in ("structure_event", "volume_expansion")
            if self._available(dna, availability, name)
            and getattr(dna, name) >= policy.material_factor_threshold
        )
        if not (
            initiating
            and self._available(dna, availability, "momentum_shift")
            and dna.momentum_shift < policy.weak_confirmation_threshold
            and dna.detection_confidence >= policy.minimum_detection_confidence
        ):
            return ()
        basis = tuple(self._basis_factor(dna, name) for name in initiating) + (
            self._basis_factor(dna, "momentum_shift"),
            "detection_confidence={0}".format(_number(dna.detection_confidence)),
        )
        return (_RuleOutput(
            2,
            "momentum_confirmation",
            ExpectationKind.CONFIRMATION,
            ExpectationStrength.MEDIUM,
            "momentum_shift",
            "Measured initiating activity is present; future measured momentum confirmation is expected within the evaluation window.",
            basis,
            ("Momentum Shift should rise to at least {0} while measured within the window.".format(_number(policy.weak_confirmation_threshold)),),
            (
                "The window expires without measured Momentum Shift confirmation.",
                "All measured initiating factors fall below {0}.".format(_number(policy.material_factor_threshold)),
            ),
            policy.default_window_minutes,
            {
                "target_factor": "momentum_shift",
                "confirmation_threshold": policy.weak_confirmation_threshold,
                "initiating_factors": initiating,
                "initiating_factor_threshold": policy.material_factor_threshold,
                "contradiction_threshold": policy.material_factor_threshold,
                "minimum_coverage_ratio": EVALUATION_MINIMUM_COVERAGE_RATIO,
            },
        ),)

    def _factor_persistence(self, dna: SituationDNA, availability: TypingMapping[str, str]) -> Tuple[_RuleOutput, ...]:
        policy = self._policy
        outputs = []
        for name in ("whale_activity", "funding_divergence", "structure_event", "volume_expansion"):
            if not self._available(dna, availability, name) or getattr(dna, name) < policy.strong_factor_threshold:
                continue
            outputs.append(_RuleOutput(
                3,
                "factor_persistence",
                ExpectationKind.FACTOR_PERSISTENCE,
                ExpectationStrength.HIGH,
                name,
                "The currently strong measured {0} condition is expected to remain materially present during the evaluation window.".format(FACTOR_LABELS[name]),
                (self._basis_factor(dna, name),),
                ("{0} should remain measured at or above {1} during the window.".format(FACTOR_LABELS[name], _number(policy.material_factor_threshold)),),
                (
                    "{0} becomes unavailable during the window.".format(FACTOR_LABELS[name]),
                    "Measured {0} falls below {1}.".format(FACTOR_LABELS[name], _number(policy.material_factor_threshold)),
                ),
                policy.short_window_minutes,
                {
                    "target_factor": name,
                    "persistence_threshold": policy.material_factor_threshold,
                    "contradiction_threshold": policy.material_factor_threshold,
                    "minimum_required_later_entries": 1,
                },
            ))
        return tuple(outputs)

    def _factor_appearance(self, dna: SituationDNA, availability: TypingMapping[str, str]) -> Tuple[_RuleOutput, ...]:
        policy = self._policy
        if not (
            self._available(dna, availability, "structure_event")
            and dna.structure_event >= policy.strong_factor_threshold
            and self._available(dna, availability, "volume_expansion")
            and dna.volume_expansion >= policy.strong_factor_threshold
            and availability.get("funding_divergence") == MISSING
            and dna.funding_divergence is None
            and dna.detection_confidence >= policy.minimum_detection_confidence
        ):
            return ()
        return (_RuleOutput(
            4,
            "funding_appearance_after_structure_volume",
            ExpectationKind.FACTOR_APPEARANCE,
            ExpectationStrength.MEDIUM,
            "funding_divergence",
            "Strong measured structure and volume activity provide the approved rationale to watch for a future Funding Divergence measurement.",
            (
                self._basis_factor(dna, "structure_event"),
                self._basis_factor(dna, "volume_expansion"),
                "funding_divergence=MISSING",
                "detection_confidence={0}".format(_number(dna.detection_confidence)),
            ),
            ("Funding Divergence should become AVAILABLE with a measured value during the window.",),
            (
                "The window expires while Funding Divergence remains MISSING.",
                "Structure Event or Volume Expansion loses measured strong-factor support.",
            ),
            policy.long_window_minutes,
            {
                "target_factor": "funding_divergence",
                "source_required_availability": "MISSING",
                "fulfillment_availability": "AVAILABLE",
                "missing_confirmation_availability": "MISSING",
                "disqualifying_availability_states": (
                    "ERROR",
                    "STALE",
                    "UNSUPPORTED",
                ),
                "minimum_required_later_entries": 1,
            },
        ),)

    def _stage_advance(
        self,
        stage: EmergingStage,
        dna: SituationDNA,
        availability: TypingMapping[str, str],
        supporting_factors: Tuple[str, ...],
    ) -> Tuple[_RuleOutput, ...]:
        policy = self._policy
        next_stage = {
            EmergingStage.SEED: EmergingStage.EMERGING,
            EmergingStage.EMERGING: EmergingStage.BUILDING,
        }.get(stage)
        measured_support = tuple(
            name for name in supporting_factors
            if name in FACTOR_FIELDS and self._available(dna, availability, name)
        )
        if not (
            next_stage is not None
            and dna.emergence >= policy.strong_factor_threshold
            and dna.horizon >= policy.strong_factor_threshold
            and dna.detection_confidence >= policy.minimum_detection_confidence
            and len(set(measured_support)) >= 2
        ):
            return ()
        basis = (
            "stage={0}".format(stage.value),
            "emergence={0}".format(_number(dna.emergence)),
            "horizon={0}".format(_number(dna.horizon)),
            "detection_confidence={0}".format(_number(dna.detection_confidence)),
        ) + tuple(self._basis_factor(dna, name) for name in sorted(set(measured_support)))
        return (_RuleOutput(
            5,
            "stage_advance_{0}_to_{1}".format(stage.value.lower(), next_stage.value.lower()),
            ExpectationKind.STAGE_ADVANCE,
            ExpectationStrength.HIGH,
            next_stage.value,
            "The current measured situation may advance by one descriptive lifecycle stage within the evaluation window.",
            basis,
            ("A future Timeline entry should record stage {0} with measured supporting evidence.".format(next_stage.value),),
            (
                "The window expires without a measured stage advance.",
                "Emergence, Horizon, or independent measured support falls below the configured requirement.",
            ),
            policy.long_window_minutes,
            {
                "source_stage": stage.value,
                "expected_target_stage": next_stage.value,
                "incompatible_stages": self._incompatible_advance_stages(
                    stage,
                    next_stage,
                ),
                "minimum_required_later_entries": 1,
            },
        ),)

    def _stage_persistence(
        self,
        stage: EmergingStage,
        dna: SituationDNA,
        availability: TypingMapping[str, str],
        supporting_factors: Tuple[str, ...],
        advance_generated: bool,
    ) -> Tuple[_RuleOutput, ...]:
        policy = self._policy
        measured_support = tuple(
            name for name in supporting_factors
            if name in FACTOR_FIELDS and self._available(dna, availability, name)
        )
        if not (
            not advance_generated
            and stage in (EmergingStage.SEED, EmergingStage.EMERGING, EmergingStage.BUILDING)
            and dna.maturity < policy.high_maturity_threshold
            and dna.horizon > policy.low_horizon_threshold
            and dna.detection_confidence >= policy.minimum_detection_confidence
            and measured_support
        ):
            return ()
        return (_RuleOutput(
            6,
            "stage_persistence_{0}".format(stage.value.lower()),
            ExpectationKind.STAGE_PERSISTENCE,
            ExpectationStrength.LOW,
            stage.value,
            "Current measured evidence is stable but insufficient for a configured stage advance, so stage persistence is expected during the window.",
            (
                "stage={0}".format(stage.value),
                "maturity={0}".format(_number(dna.maturity)),
                "horizon={0}".format(_number(dna.horizon)),
                "detection_confidence={0}".format(_number(dna.detection_confidence)),
            ) + tuple(self._basis_factor(dna, name) for name in sorted(set(measured_support))),
            ("A future Timeline entry should continue to record stage {0} during the window.".format(stage.value),),
            (
                "A future Timeline entry records a different measured stage.",
                "Maturity or Horizon crosses a configured transition-risk threshold.",
            ),
            policy.default_window_minutes,
            {
                "source_stage": stage.value,
                "required_stage": stage.value,
                "minimum_required_later_entries": 1,
            },
        ),)

    def _invalidation_risk(
        self,
        stage: EmergingStage,
        dna: SituationDNA,
        availability: TypingMapping[str, str],
        supporting_factors: Tuple[str, ...],
    ) -> Tuple[_RuleOutput, ...]:
        policy = self._policy
        high_maturity = dna.maturity >= policy.high_maturity_threshold
        low_horizon = dna.horizon <= policy.low_horizon_threshold
        measured_support = tuple(
            name for name in supporting_factors
            if name in FACTOR_FIELDS and self._available(dna, availability, name)
        )
        concentration = len(set(measured_support)) == 1
        weakening = (
            self._available(dna, availability, "structure_event")
            and dna.structure_event >= policy.material_factor_threshold
            and any(
                self._available(dna, availability, name)
                and getattr(dna, name) < policy.weak_confirmation_threshold
                for name in ("volume_expansion", "momentum_shift")
            )
        )
        if not (high_maturity or low_horizon or concentration or weakening):
            return ()
        basis = [
            "stage={0}".format(stage.value),
            "maturity={0}".format(_number(dna.maturity)),
            "horizon={0}".format(_number(dna.horizon)),
        ]
        if concentration:
            basis.append("measured_supporting_factor_count=1")
        if weakening:
            basis.append("measured_confirmation_below={0}".format(_number(policy.weak_confirmation_threshold)))
        strength = ExpectationStrength.HIGH if high_maturity and low_horizon else ExpectationStrength.MEDIUM
        return (_RuleOutput(
            7,
            "invalidation_risk",
            ExpectationKind.INVALIDATION_RISK,
            strength,
            "current_stage_classification",
            "Current measured limitations create a descriptive risk that the situation may not maintain its present classification.",
            tuple(basis),
            ("A future Timeline entry should preserve sufficient measured evidence for the current classification.",),
            (
                "Measured support weakens further or becomes unavailable.",
                "A future Timeline entry records a classification change during the window.",
            ),
            policy.short_window_minutes,
            {
                "maturity_threshold": policy.high_maturity_threshold,
                "horizon_threshold": policy.low_horizon_threshold,
                "concentration_threshold": 1,
                "strengthening_thresholds": {
                    "minimum_emergence_increase": EVALUATION_MATERIAL_CHANGE_THRESHOLD,
                    "minimum_horizon_increase": EVALUATION_MATERIAL_CHANGE_THRESHOLD,
                    "minimum_supporting_factor_count": 2,
                },
                "weakening_thresholds": {
                    "material_change_threshold": EVALUATION_MATERIAL_CHANGE_THRESHOLD,
                    "sharp_change_threshold": EVALUATION_SHARP_CHANGE_THRESHOLD,
                },
            },
        ),)

    @staticmethod
    def _incompatible_advance_stages(
        source_stage: EmergingStage,
        target_stage: EmergingStage,
    ) -> Tuple[str, ...]:
        ordered = (
            EmergingStage.UNKNOWN,
            EmergingStage.SEED,
            EmergingStage.EMERGING,
            EmergingStage.BUILDING,
            EmergingStage.MATURE,
            EmergingStage.EXHAUSTED,
        )
        return tuple(
            stage.value
            for stage in ordered
            if stage not in (source_stage, target_stage)
        )


def _number(value: float) -> str:
    return "{0:g}".format(round(float(value), 6))


def _display_subject(expectation: SituationExpectation) -> str:
    if expectation.subject in FACTOR_LABELS:
        if expectation.kind is ExpectationKind.CONFIRMATION:
            return "{0} confirmation".format(FACTOR_LABELS[expectation.subject])
        if expectation.kind is ExpectationKind.FACTOR_PERSISTENCE:
            return "{0} persistence".format(FACTOR_LABELS[expectation.subject])
        if expectation.kind is ExpectationKind.FACTOR_APPEARANCE:
            return "{0} appearance".format(FACTOR_LABELS[expectation.subject])
        return FACTOR_LABELS[expectation.subject]
    if expectation.kind is ExpectationKind.STAGE_ADVANCE:
        return "Stage advance to {0}".format(expectation.subject)
    if expectation.kind is ExpectationKind.STAGE_PERSISTENCE:
        return "Stage persistence at {0}".format(expectation.subject)
    return expectation.subject.replace("_", " ").title()


def format_situation_expectation(expectation: SituationExpectation) -> str:
    """Render one hypothesis as plain text without evaluation or trade advice."""

    if not isinstance(expectation, SituationExpectation):
        raise TypeError("expectation must be a SituationExpectation")
    lines = [
        expectation.asset,
        "",
        "Expectation: {0}".format(_display_subject(expectation)),
        "Strength: {0}".format(expectation.strength.value),
        "Window: {0}-{1} UTC".format(
            expectation.window_start.strftime("%H:%M"),
            expectation.window_end.strftime("%H:%M"),
        ),
        "",
        "Basis:",
    ]
    lines.extend("- {0}".format(item) for item in expectation.basis)
    lines.extend(["", "Expected:"])
    lines.extend("- {0}".format(item) for item in expectation.fulfillment_criteria)
    lines.extend(["", "Contradicted if:"])
    lines.extend("- {0}".format(item) for item in expectation.contradiction_criteria)
    lines.extend(["", "Status:", "- NOT EVALUATED"])
    return "\n".join(lines)


def format_situation_expectations(expectations: Tuple[SituationExpectation, ...]) -> str:
    """Render a deterministic collection of hypotheses."""

    if isinstance(expectations, (str, bytes, set, frozenset)):
        raise TypeError("expectations must be an ordered collection")
    values = tuple(expectations)
    if not all(isinstance(item, SituationExpectation) for item in values):
        raise TypeError("expectations must contain SituationExpectation objects")
    if not values:
        return "No valid expectations."
    return "\n\n".join(format_situation_expectation(item) for item in values)


__all__ = [
    "ExpectationKind",
    "ExpectationPolicy",
    "ExpectationStrength",
    "SituationExpectation",
    "SituationExpectationEngine",
    "deterministic_expectation_id",
    "format_situation_expectation",
    "format_situation_expectations",
]
