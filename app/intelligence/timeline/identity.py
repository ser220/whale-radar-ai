"""Deterministic Phase 1 identity continuity for Market Situation timelines."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import timedelta
from types import MappingProxyType
from typing import Any, Dict, Mapping as TypingMapping, Optional, Tuple

from app.intelligence.early_bird import EmergingStage
from app.intelligence.timeline.models import (
    MarketSituationTimeline,
    SituationDNA,
    _frozen_mapping,
    _mapping_payload,
    _percentage,
    _required_text,
    _to_plain,
)


IDENTITY_POLICY_VERSION = 1
DEFAULT_MAX_TIME_GAP = timedelta(hours=6)
DEFAULT_MATCH_THRESHOLD = 65.0

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

EVOLUTION_FIELDS = (
    "emergence",
    "horizon",
    "detection_confidence",
    "opportunity",
    "priority",
    "maturity",
)

CRITERION_WEIGHTS = MappingProxyType({
    "time_continuity": 0.10,
    "stage_compatibility": 0.15,
    "dna_continuity": 0.30,
    "supporting_factor_continuity": 0.15,
    "limiting_factor_continuity": 0.05,
    "evolution_continuity": 0.25,
})

_STAGE_INDEX = MappingProxyType({
    EmergingStage.SEED: 0,
    EmergingStage.EMERGING: 1,
    EmergingStage.BUILDING: 2,
    EmergingStage.MATURE: 3,
    EmergingStage.EXHAUSTED: 4,
})


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


def _bounded(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 6)


def _jaccard(left: Tuple[str, ...], right: Tuple[str, ...]) -> float:
    left_values = set(left)
    right_values = set(right)
    union = left_values | right_values
    if not union:
        return 0.0
    return round(len(left_values & right_values) / len(union) * 100.0, 6)


def _metric_continuity(left: float, right: float) -> float:
    return _bounded(100.0 - abs(float(left) - float(right)))


@dataclass(frozen=True)
class SituationIdentityResult:
    """Immutable answer describing whether a candidate continues a timeline."""

    matched: bool
    confidence: float
    reason: str
    matched_timeline_id: Optional[str]
    matched_version: Optional[int]
    candidate_timeline_id: str
    metadata: TypingMapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.matched, bool):
            raise TypeError("matched must be a boolean")
        object.__setattr__(
            self,
            "confidence",
            _percentage(self.confidence, "confidence"),
        )
        object.__setattr__(self, "reason", _required_text(self.reason, "reason"))
        object.__setattr__(
            self,
            "matched_timeline_id",
            _optional_text(self.matched_timeline_id, "matched_timeline_id"),
        )
        object.__setattr__(
            self,
            "matched_version",
            _optional_version(self.matched_version, "matched_version"),
        )
        object.__setattr__(
            self,
            "candidate_timeline_id",
            _required_text(self.candidate_timeline_id, "candidate_timeline_id"),
        )
        if self.matched:
            if self.matched_timeline_id is None or self.matched_version is None:
                raise ValueError("matched result requires timeline ID and version")
        elif self.matched_timeline_id is not None or self.matched_version is not None:
            raise ValueError("unmatched result must not identify a matched timeline")
        object.__setattr__(
            self,
            "metadata",
            _frozen_mapping(self.metadata, "metadata"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matched": self.matched,
            "confidence": self.confidence,
            "reason": self.reason,
            "matched_timeline_id": self.matched_timeline_id,
            "matched_version": self.matched_version,
            "candidate_timeline_id": self.candidate_timeline_id,
            "metadata": _to_plain(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: TypingMapping[str, Any]) -> "SituationIdentityResult":
        return cls(**_mapping_payload(data, "situation identity result"))


class SituationIdentityEngine:
    """Evaluate identity continuity without modifying either input timeline."""

    def __init__(
        self,
        *,
        max_time_gap: timedelta = DEFAULT_MAX_TIME_GAP,
        match_threshold: float = DEFAULT_MATCH_THRESHOLD
    ) -> None:
        if not isinstance(max_time_gap, timedelta):
            raise TypeError("max_time_gap must be a timedelta")
        if max_time_gap.total_seconds() <= 0.0:
            raise ValueError("max_time_gap must be positive")
        self._max_time_gap = max_time_gap
        self._match_threshold = _percentage(match_threshold, "match_threshold")

    def evaluate(
        self,
        existing_timeline: MarketSituationTimeline,
        new_timeline: MarketSituationTimeline,
    ) -> SituationIdentityResult:
        self._validate_inputs(existing_timeline, new_timeline)
        candidate_id = new_timeline.timeline_id

        if existing_timeline.asset != new_timeline.asset:
            return self._hard_rejection(
                existing_timeline,
                new_timeline,
                "Different assets cannot share a Market Situation identity.",
                "asset_mismatch",
            )
        if existing_timeline.current_stage is EmergingStage.EXHAUSTED:
            return self._hard_rejection(
                existing_timeline,
                new_timeline,
                "An exhausted timeline cannot accept identity continuation.",
                "existing_timeline_exhausted",
            )
        if self._is_closed(existing_timeline):
            return self._hard_rejection(
                existing_timeline,
                new_timeline,
                "A closed timeline cannot accept identity continuation.",
                "existing_timeline_closed",
            )

        new_entry = new_timeline.entries[0]
        time_gap = new_entry.created_at - existing_timeline.updated_at
        if time_gap.total_seconds() < 0.0:
            return self._hard_rejection(
                existing_timeline,
                new_timeline,
                "Candidate evidence predates the existing timeline state.",
                "time_regression",
                time_gap_seconds=time_gap.total_seconds(),
            )
        if time_gap > self._max_time_gap:
            return self._hard_rejection(
                existing_timeline,
                new_timeline,
                "The configured continuity time gap was exceeded.",
                "time_gap_exceeded",
                time_gap_seconds=time_gap.total_seconds(),
            )

        existing_entry = existing_timeline.entries[-1]
        criteria = self._criteria(
            existing_entry.dna,
            new_entry.dna,
            existing_timeline.current_stage,
            new_timeline.current_stage,
            existing_entry.supporting_factors,
            new_entry.supporting_factors,
            existing_entry.limiting_factors,
            new_entry.limiting_factors,
            time_gap,
        )
        continuity_score = _bounded(
            sum(criteria[name] * weight for name, weight in CRITERION_WEIGHTS.items())
        )
        matched = continuity_score >= self._match_threshold
        decision = "matched" if matched else "new_situation"
        reason = self._reason(matched, continuity_score, criteria)
        return SituationIdentityResult(
            matched=matched,
            confidence=continuity_score,
            reason=reason,
            matched_timeline_id=(existing_timeline.timeline_id if matched else None),
            matched_version=(existing_timeline.version if matched else None),
            candidate_timeline_id=candidate_id,
            metadata={
                "identity_policy_version": IDENTITY_POLICY_VERSION,
                "decision": decision,
                "hard_rejection": False,
                "criteria": criteria,
                "criterion_weights": CRITERION_WEIGHTS,
                "match_threshold": self._match_threshold,
                "max_time_gap_seconds": self._max_time_gap.total_seconds(),
                "time_gap_seconds": time_gap.total_seconds(),
                "existing_stage": existing_timeline.current_stage.value,
                "candidate_stage": new_timeline.current_stage.value,
                "confidence_semantics": "identity_match_continuity",
            },
        )

    @staticmethod
    def _validate_inputs(
        existing_timeline: Any,
        new_timeline: Any,
    ) -> None:
        if not isinstance(existing_timeline, MarketSituationTimeline):
            raise TypeError("existing_timeline must be a MarketSituationTimeline")
        if not isinstance(new_timeline, MarketSituationTimeline):
            raise TypeError("new_timeline must be a MarketSituationTimeline")
        if not existing_timeline.entries:
            raise ValueError("existing_timeline must contain at least one entry")
        if new_timeline.version != 1 or len(new_timeline.entries) != 1:
            raise ValueError("new_timeline must be version 1 with exactly one entry")

    @staticmethod
    def _is_closed(timeline: MarketSituationTimeline) -> bool:
        if timeline.metadata.get("closed") is True:
            return True
        status = timeline.metadata.get("status")
        return isinstance(status, str) and status.strip().upper() == "CLOSED"

    def _hard_rejection(
        self,
        existing_timeline: MarketSituationTimeline,
        new_timeline: MarketSituationTimeline,
        reason: str,
        code: str,
        *,
        time_gap_seconds: Optional[float] = None
    ) -> SituationIdentityResult:
        metadata = {
            "identity_policy_version": IDENTITY_POLICY_VERSION,
            "decision": "new_situation",
            "hard_rejection": True,
            "rejection_code": code,
            "match_threshold": self._match_threshold,
            "max_time_gap_seconds": self._max_time_gap.total_seconds(),
            "existing_stage": existing_timeline.current_stage.value,
            "candidate_stage": new_timeline.current_stage.value,
            "confidence_semantics": "identity_match_continuity",
        }
        if time_gap_seconds is not None:
            metadata["time_gap_seconds"] = time_gap_seconds
        return SituationIdentityResult(
            matched=False,
            confidence=0.0,
            reason=reason,
            matched_timeline_id=None,
            matched_version=None,
            candidate_timeline_id=new_timeline.timeline_id,
            metadata=metadata,
        )

    def _criteria(
        self,
        existing_dna: SituationDNA,
        candidate_dna: SituationDNA,
        existing_stage: EmergingStage,
        candidate_stage: EmergingStage,
        existing_supporting: Tuple[str, ...],
        candidate_supporting: Tuple[str, ...],
        existing_limiting: Tuple[str, ...],
        candidate_limiting: Tuple[str, ...],
        time_gap: timedelta,
    ) -> Dict[str, float]:
        gap_fraction = time_gap.total_seconds() / self._max_time_gap.total_seconds()
        return {
            "time_continuity": _bounded(100.0 * (1.0 - gap_fraction)),
            "stage_compatibility": self._stage_compatibility(
                existing_stage,
                candidate_stage,
            ),
            "dna_continuity": self._dna_continuity(existing_dna, candidate_dna),
            "supporting_factor_continuity": _jaccard(
                existing_supporting,
                candidate_supporting,
            ),
            "limiting_factor_continuity": _jaccard(
                existing_limiting,
                candidate_limiting,
            ),
            "evolution_continuity": self._evolution_continuity(
                existing_dna,
                candidate_dna,
            ),
        }

    @staticmethod
    def _stage_compatibility(
        existing_stage: EmergingStage,
        candidate_stage: EmergingStage,
    ) -> float:
        if existing_stage is candidate_stage:
            return 100.0
        if (
            existing_stage is EmergingStage.UNKNOWN
            or candidate_stage is EmergingStage.UNKNOWN
        ):
            return 50.0
        difference = _STAGE_INDEX[candidate_stage] - _STAGE_INDEX[existing_stage]
        if difference == 1:
            return 100.0
        if difference == 2:
            return 70.0
        if difference == -1:
            return 55.0
        return 20.0

    @staticmethod
    def _dna_continuity(existing: SituationDNA, candidate: SituationDNA) -> float:
        existing_available = tuple(
            name for name in FACTOR_FIELDS if getattr(existing, name) is not None
        )
        candidate_available = tuple(
            name for name in FACTOR_FIELDS if getattr(candidate, name) is not None
        )
        common = tuple(
            name
            for name in FACTOR_FIELDS
            if name in existing_available and name in candidate_available
        )
        if not common:
            return 0.0
        value_continuity = sum(
            _metric_continuity(getattr(existing, name), getattr(candidate, name))
            for name in common
        ) / len(common)
        availability_overlap = _jaccard(existing_available, candidate_available)
        return _bounded(0.60 * value_continuity + 0.40 * availability_overlap)

    @staticmethod
    def _evolution_continuity(
        existing: SituationDNA,
        candidate: SituationDNA,
    ) -> float:
        return _bounded(
            sum(
                _metric_continuity(getattr(existing, name), getattr(candidate, name))
                for name in EVOLUTION_FIELDS
            )
            / len(EVOLUTION_FIELDS)
        )

    def _reason(
        self,
        matched: bool,
        score: float,
        criteria: TypingMapping[str, float],
    ) -> str:
        prefix = "Matched existing timeline" if matched else "New situation"
        relation = "met" if matched else "did not meet"
        return (
            "{0}: continuity {1:.2f} {2} threshold {3:.2f}; "
            "DNA {4:.2f}, stage {5:.2f}, supporting factors {6:.2f}."
        ).format(
            prefix,
            score,
            relation,
            self._match_threshold,
            criteria["dna_continuity"],
            criteria["stage_compatibility"],
            criteria["supporting_factor_continuity"],
        )


__all__ = [
    "SituationIdentityEngine",
    "SituationIdentityResult",
]
