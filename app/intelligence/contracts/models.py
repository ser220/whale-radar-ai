"""Immutable value models for intelligence inputs and outputs."""

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Tuple, Type, TypeVar

from app.intelligence.contracts._validation import (
    bounded_percentage,
    frozen_mapping,
    optional_string,
    parse_datetime,
    required_string,
    string_tuple,
    to_plain,
    utc_datetime,
    utc_now,
)
from app.intelligence.contracts.enums import Direction, LifecycleState, TrendState


ModelT = TypeVar("ModelT")


def _enum_value(enum_type: Type[ModelT], value: Any, field_name: str) -> ModelT:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {field_name}: {value!r}") from exc


@dataclass(frozen=True)
class ExpertOpinion:
    expert_name: str
    direction: Direction
    state: str
    score: float
    confidence: float
    quality: float
    reasons: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    timestamp: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "expert_name", required_string(self.expert_name, "expert_name"))
        object.__setattr__(self, "direction", _enum_value(Direction, self.direction, "direction"))
        object.__setattr__(self, "state", required_string(self.state, "state"))
        object.__setattr__(self, "score", bounded_percentage(self.score, "score"))
        object.__setattr__(self, "confidence", bounded_percentage(self.confidence, "confidence"))
        object.__setattr__(self, "quality", bounded_percentage(self.quality, "quality"))
        object.__setattr__(self, "reasons", string_tuple(self.reasons, "reasons"))
        object.__setattr__(self, "warnings", string_tuple(self.warnings, "warnings"))
        object.__setattr__(self, "metadata", frozen_mapping(self.metadata, "metadata"))
        object.__setattr__(self, "timestamp", utc_datetime(self.timestamp))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expert_name": self.expert_name,
            "direction": self.direction.value,
            "state": self.state,
            "score": self.score,
            "confidence": self.confidence,
            "quality": self.quality,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "metadata": to_plain(self.metadata),
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExpertOpinion":
        payload = dict(data)
        payload["direction"] = _enum_value(Direction, payload.get("direction"), "direction")
        payload["timestamp"] = parse_datetime(payload.get("timestamp"))
        return cls(**payload)


@dataclass(frozen=True)
class MarketState:
    trend: TrendState
    direction: Direction
    strength: float
    continuation_probability: float
    correction_probability: float
    reversal_probability: float
    market_maturity: float
    decision_stability: float
    overall_confidence: float
    reasons: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    timestamp: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "trend", _enum_value(TrendState, self.trend, "trend"))
        object.__setattr__(self, "direction", _enum_value(Direction, self.direction, "direction"))
        for field_name in (
            "strength",
            "continuation_probability",
            "correction_probability",
            "reversal_probability",
            "market_maturity",
            "decision_stability",
            "overall_confidence",
        ):
            object.__setattr__(self, field_name, bounded_percentage(getattr(self, field_name), field_name))
        object.__setattr__(self, "reasons", string_tuple(self.reasons, "reasons"))
        object.__setattr__(self, "warnings", string_tuple(self.warnings, "warnings"))
        object.__setattr__(self, "timestamp", utc_datetime(self.timestamp))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trend": self.trend.value,
            "direction": self.direction.value,
            "strength": self.strength,
            "continuation_probability": self.continuation_probability,
            "correction_probability": self.correction_probability,
            "reversal_probability": self.reversal_probability,
            "market_maturity": self.market_maturity,
            "decision_stability": self.decision_stability,
            "overall_confidence": self.overall_confidence,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MarketState":
        payload = dict(data)
        payload["trend"] = _enum_value(TrendState, payload.get("trend"), "trend")
        payload["direction"] = _enum_value(Direction, payload.get("direction"), "direction")
        payload["timestamp"] = parse_datetime(payload.get("timestamp"))
        return cls(**payload)


@dataclass(frozen=True)
class DecisionState:
    stage: LifecycleState
    trade_readiness: float
    eta: Optional[str]
    risk: str
    confidence: float
    action: str
    missing_confirmations: Tuple[str, ...] = ()
    timestamp: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "stage", _enum_value(LifecycleState, self.stage, "stage"))
        object.__setattr__(self, "trade_readiness", bounded_percentage(self.trade_readiness, "trade_readiness"))
        object.__setattr__(self, "eta", optional_string(self.eta, "eta"))
        object.__setattr__(self, "risk", required_string(self.risk, "risk"))
        object.__setattr__(self, "confidence", bounded_percentage(self.confidence, "confidence"))
        object.__setattr__(self, "action", required_string(self.action, "action"))
        object.__setattr__(
            self,
            "missing_confirmations",
            string_tuple(self.missing_confirmations, "missing_confirmations"),
        )
        object.__setattr__(self, "timestamp", utc_datetime(self.timestamp))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "trade_readiness": self.trade_readiness,
            "eta": self.eta,
            "risk": self.risk,
            "confidence": self.confidence,
            "action": self.action,
            "missing_confirmations": list(self.missing_confirmations),
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DecisionState":
        payload = dict(data)
        payload["stage"] = _enum_value(LifecycleState, payload.get("stage"), "stage")
        payload["timestamp"] = parse_datetime(payload.get("timestamp"))
        return cls(**payload)
