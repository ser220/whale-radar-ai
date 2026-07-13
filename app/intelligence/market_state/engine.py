"""Pure deterministic synthesis of ExpertOpinion values into MarketState."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import math
from numbers import Real
from typing import Dict, List, Optional, Sequence, Set, Tuple

from app.intelligence.contracts import Direction, ExpertOpinion, MarketState, TrendState
from app.intelligence.market_state.policy import SynthesisPolicy


@dataclass(frozen=True)
class _Contribution:
    opinion: ExpertOpinion
    configured_weight: float
    quality_weight: float
    effective_weight: float
    state: TrendState


class MarketStateEngine:
    """Aggregate already-produced expert opinions using a documented policy."""

    def __init__(self, policy: Optional[SynthesisPolicy] = None) -> None:
        if policy is not None and not isinstance(policy, SynthesisPolicy):
            raise TypeError("policy must be a SynthesisPolicy")
        self._policy = policy or SynthesisPolicy()

    @property
    def policy(self) -> SynthesisPolicy:
        return self._policy

    def synthesize(
        self,
        opinions: Iterable[ExpertOpinion],
        *,
        weights: Optional[Mapping[str, float]] = None,
        timestamp: Optional[datetime] = None,
    ) -> MarketState:
        resolved_timestamp = self._timestamp(timestamp)
        opinion_values = self._opinions(opinions)
        configured_weights = self._weights(weights)
        self._reject_duplicates(opinion_values)

        opinion_names = {opinion.expert_name for opinion in opinion_values}
        unknown_weight_names = sorted(set(configured_weights) - opinion_names)

        if not opinion_values:
            warnings = ["No expert opinions were supplied."]
            warnings.extend(
                f"Configured weight for unknown expert '{name}' was ignored."
                for name in unknown_weight_names
            )
            return self._empty_state(resolved_timestamp, warnings)

        contributions = tuple(
            self._contribution(opinion, configured_weights.get(opinion.expert_name, 1.0))
            for opinion in opinion_values
        )
        contributors = tuple(item for item in contributions if item.effective_weight > 0.0)
        total_effective_weight = sum(item.effective_weight for item in contributors)

        reasons = self._source_messages(contributors, "reasons", self._policy.reason_limit)
        source_warnings = self._source_messages(
            contributors, "warnings", self._policy.warning_limit
        )
        contextual_warnings: List[str] = []
        contextual_warnings.extend(
            f"Configured weight for unknown expert '{name}' was ignored."
            for name in unknown_weight_names
        )
        contextual_warnings.extend(self._unsupported_state_warnings(contributors))

        if total_effective_weight <= 0.0:
            warnings = [
                "No expert opinions had positive effective weight.",
                "Insufficient contributors: fewer than two positively weighted opinions.",
            ]
            aggregate_quality = self._aggregate_quality(contributions)
            if aggregate_quality < self._policy.low_quality_threshold:
                warnings.append(
                    f"Low aggregate quality: {aggregate_quality:.2f} is below "
                    f"{self._policy.low_quality_threshold:.2f}."
                )
            warnings.extend(contextual_warnings)
            warnings.extend(source_warnings)
            return self._empty_state(resolved_timestamp, warnings, reasons)

        direction_support = self._direction_support(contributors)
        directional_balance = (
            direction_support[Direction.BULLISH] - direction_support[Direction.BEARISH]
        ) / total_effective_weight
        direction = self._direction(directional_balance)

        state_support = self._state_support(contributors)
        trend = self._trend(state_support, total_effective_weight)

        strength = self._weighted_mean(
            contributors,
            lambda item: item.opinion.score,
            lambda item: item.effective_weight,
        )
        overall_confidence = self._weighted_mean(
            contributions,
            lambda item: item.opinion.confidence,
            lambda item: item.quality_weight,
        )
        aggregate_quality = self._aggregate_quality(contributions)
        continuation_probability = self._support_percentage(
            state_support[TrendState.TREND], total_effective_weight
        )
        correction_probability = self._support_percentage(
            state_support[TrendState.CORRECTION], total_effective_weight
        )
        reversal_probability = self._support_percentage(
            state_support[TrendState.REVERSAL], total_effective_weight
        )
        market_maturity = self._weighted_mean(
            contributors,
            lambda item: (
                0.50 * item.opinion.score
                + 0.30 * item.opinion.confidence
                + 0.20 * item.opinion.quality
            ),
            lambda item: item.effective_weight,
        )
        decision_stability = self._decision_stability(
            contributors=contributors,
            total_effective_weight=total_effective_weight,
            direction_support=direction_support,
            state_support=state_support,
            overall_confidence=overall_confidence,
            aggregate_quality=aggregate_quality,
        )

        warnings: List[str] = []
        self._add_synthesis_warnings(
            warnings=warnings,
            contributors=contributors,
            total_effective_weight=total_effective_weight,
            direction_support=direction_support,
            state_support=state_support,
            trend=trend,
            aggregate_quality=aggregate_quality,
        )
        warnings.extend(contextual_warnings)
        warnings.extend(source_warnings)

        return MarketState(
            trend=trend,
            direction=direction,
            strength=self._metric(strength),
            continuation_probability=self._metric(continuation_probability),
            correction_probability=self._metric(correction_probability),
            reversal_probability=self._metric(reversal_probability),
            market_maturity=self._metric(market_maturity),
            decision_stability=self._metric(decision_stability),
            overall_confidence=self._metric(overall_confidence),
            reasons=reasons,
            warnings=self._deduplicate(warnings, self._policy.warning_limit),
            timestamp=resolved_timestamp,
        )

    @staticmethod
    def _timestamp(value: Optional[datetime]) -> datetime:
        if value is None:
            return datetime.now(timezone.utc)
        if not isinstance(value, datetime):
            raise TypeError("timestamp must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return value.astimezone(timezone.utc)

    @staticmethod
    def _opinions(values: Iterable[ExpertOpinion]) -> Tuple[ExpertOpinion, ...]:
        if not isinstance(values, Iterable):
            raise TypeError("opinions must be an iterable of ExpertOpinion objects")

        opinions: List[ExpertOpinion] = []
        for value in values:
            if not isinstance(value, ExpertOpinion):
                raise TypeError("opinions must contain only ExpertOpinion objects")
            opinions.append(value)
        return tuple(opinions)

    @staticmethod
    def _weights(values: Optional[Mapping[str, float]]) -> Dict[str, float]:
        if values is None:
            return {}
        if not isinstance(values, Mapping):
            raise TypeError("weights must be a mapping of expert names to numbers")

        weights: Dict[str, float] = {}
        for expert_name, value in values.items():
            if not isinstance(expert_name, str) or not expert_name.strip():
                raise ValueError("weight keys must be non-empty expert names")
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"weight for '{expert_name}' must be a real number")
            normalized = float(value)
            if not math.isfinite(normalized) or normalized < 0.0:
                raise ValueError(f"weight for '{expert_name}' must be finite and non-negative")
            weights[expert_name] = normalized
        return weights

    @staticmethod
    def _reject_duplicates(opinions: Sequence[ExpertOpinion]) -> None:
        seen: Set[str] = set()
        for opinion in opinions:
            if opinion.expert_name in seen:
                raise ValueError(f"duplicate expert opinion: {opinion.expert_name}")
            seen.add(opinion.expert_name)

    @staticmethod
    def _canonical_state(value: str) -> TrendState:
        normalized = value.strip().upper()
        try:
            return TrendState(normalized)
        except ValueError:
            return TrendState.UNKNOWN

    def _contribution(self, opinion: ExpertOpinion, configured_weight: float) -> _Contribution:
        quality_weight = configured_weight * (opinion.quality / 100.0)
        effective_weight = quality_weight * (opinion.confidence / 100.0)
        return _Contribution(
            opinion=opinion,
            configured_weight=configured_weight,
            quality_weight=quality_weight,
            effective_weight=effective_weight,
            state=self._canonical_state(opinion.state),
        )

    @staticmethod
    def _direction_support(contributors: Sequence[_Contribution]) -> Dict[Direction, float]:
        support = {direction: 0.0 for direction in Direction}
        for item in contributors:
            support[item.opinion.direction] += item.effective_weight
        return support

    @staticmethod
    def _state_support(contributors: Sequence[_Contribution]) -> Dict[TrendState, float]:
        support = {state: 0.0 for state in TrendState}
        for item in contributors:
            support[item.state] += item.effective_weight
        return support

    def _direction(self, balance: float) -> Direction:
        if balance >= self._policy.direction_threshold:
            return Direction.BULLISH
        if balance <= -self._policy.direction_threshold:
            return Direction.BEARISH
        return Direction.NEUTRAL

    def _trend(self, support: Mapping[TrendState, float], total_weight: float) -> TrendState:
        candidates = sorted(
            ((value, state) for state, value in support.items() if state is not TrendState.UNKNOWN),
            key=lambda item: (-item[0], item[1].value),
        )
        if not candidates or candidates[0][0] <= 0.0:
            return TrendState.UNKNOWN

        top_support, top_state = candidates[0]
        second_support = candidates[1][0] if len(candidates) > 1 else 0.0
        if top_support / total_weight < self._policy.state_min_support:
            return TrendState.UNKNOWN
        if (top_support - second_support) / total_weight < self._policy.state_win_margin:
            return TrendState.UNKNOWN
        return top_state

    @staticmethod
    def _weighted_mean(
        values: Sequence[_Contribution],
        value_getter,
        weight_getter,
    ) -> float:
        denominator = sum(weight_getter(item) for item in values)
        if denominator <= 0.0:
            return 0.0
        return sum(value_getter(item) * weight_getter(item) for item in values) / denominator

    def _aggregate_quality(self, contributions: Sequence[_Contribution]) -> float:
        return self._weighted_mean(
            contributions,
            lambda item: item.opinion.quality,
            lambda item: item.configured_weight,
        )

    @staticmethod
    def _support_percentage(support: float, total_weight: float) -> float:
        if total_weight <= 0.0:
            return 0.0
        return 100.0 * support / total_weight

    def _decision_stability(
        self,
        *,
        contributors: Sequence[_Contribution],
        total_effective_weight: float,
        direction_support: Mapping[Direction, float],
        state_support: Mapping[TrendState, float],
        overall_confidence: float,
        aggregate_quality: float,
    ) -> float:
        direction_agreement = max(direction_support.values()) / total_effective_weight
        non_unknown_state_support = [
            value for state, value in state_support.items() if state is not TrendState.UNKNOWN
        ]
        state_agreement = (
            max(non_unknown_state_support) / total_effective_weight
            if non_unknown_state_support
            else 0.0
        )
        contributor_factor = min(len(contributors) / 2.0, 1.0)
        consensus = (
            0.30 * direction_agreement
            + 0.25 * state_agreement
            + 0.25 * (overall_confidence / 100.0)
            + 0.20 * (aggregate_quality / 100.0)
        )
        return 100.0 * contributor_factor * consensus

    def _add_synthesis_warnings(
        self,
        *,
        warnings: List[str],
        contributors: Sequence[_Contribution],
        total_effective_weight: float,
        direction_support: Mapping[Direction, float],
        state_support: Mapping[TrendState, float],
        trend: TrendState,
        aggregate_quality: float,
    ) -> None:
        bullish_share = direction_support[Direction.BULLISH] / total_effective_weight
        bearish_share = direction_support[Direction.BEARISH] / total_effective_weight
        if (
            bullish_share >= self._policy.meaningful_direction_support
            and bearish_share >= self._policy.meaningful_direction_support
        ):
            warnings.append("Material direction conflict: bullish and bearish support are both meaningful.")

        meaningful_states = [
            state
            for state, value in state_support.items()
            if state is not TrendState.UNKNOWN
            and value / total_effective_weight >= self._policy.state_min_support
        ]
        if trend is TrendState.UNKNOWN and len(meaningful_states) > 1:
            warnings.append("State disagreement: multiple states have meaningful support without a clear winner.")

        if aggregate_quality < self._policy.low_quality_threshold:
            warnings.append(
                f"Low aggregate quality: {aggregate_quality:.2f} is below "
                f"{self._policy.low_quality_threshold:.2f}."
            )
        if len(contributors) < 2:
            warnings.append("Insufficient contributors: fewer than two positively weighted opinions.")

    @staticmethod
    def _unsupported_state_warnings(contributors: Sequence[_Contribution]) -> Tuple[str, ...]:
        warnings = []
        for item in contributors:
            normalized = item.opinion.state.strip().upper()
            if item.state is TrendState.UNKNOWN and normalized != TrendState.UNKNOWN.value:
                warnings.append(
                    f"{item.opinion.expert_name}: unsupported state "
                    f"'{item.opinion.state}' mapped to UNKNOWN."
                )
        return tuple(warnings)

    @staticmethod
    def _source_messages(
        contributors: Sequence[_Contribution], field_name: str, limit: int
    ) -> Tuple[str, ...]:
        values: List[str] = []
        seen: Set[str] = set()
        for item in contributors:
            for message in getattr(item.opinion, field_name):
                value = f"{item.opinion.expert_name}: {message}"
                if value not in seen:
                    seen.add(value)
                    values.append(value)
                if len(values) >= limit:
                    return tuple(values)
        return tuple(values)

    @staticmethod
    def _deduplicate(values: Sequence[str], limit: int) -> Tuple[str, ...]:
        result: List[str] = []
        seen: Set[str] = set()
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
            if len(result) >= limit:
                break
        return tuple(result)

    @staticmethod
    def _metric(value: float) -> float:
        return round(min(max(value, 0.0), 100.0), 6)

    def _empty_state(
        self,
        timestamp: datetime,
        warnings: Sequence[str],
        reasons: Sequence[str] = (),
    ) -> MarketState:
        return MarketState(
            trend=TrendState.UNKNOWN,
            direction=Direction.NEUTRAL,
            strength=0.0,
            continuation_probability=0.0,
            correction_probability=0.0,
            reversal_probability=0.0,
            market_maturity=0.0,
            decision_stability=0.0,
            overall_confidence=0.0,
            reasons=self._deduplicate(reasons, self._policy.reason_limit),
            warnings=self._deduplicate(warnings, self._policy.warning_limit),
            timestamp=timestamp,
        )
