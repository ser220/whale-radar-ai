"""Pure deterministic Trend Expert over normalized observations."""

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Dict, List, Mapping, Optional, Sequence, Set, Tuple

from app.intelligence.contracts import Direction, ExpertOpinion, TrendState
from app.intelligence.experts.trend.policy import TrendExpertPolicy
from app.intelligence.observations import (
    StructureBreak,
    StructureObservation,
    TrendBias,
    TrendObservation,
)


_MAX_DIRECTION_RAW = 117.0
_SUPPORTED_TIMEFRAME = re.compile(r"^[1-9][0-9]*(m|h|d|w)$")


@dataclass(frozen=True)
class _Evidence:
    bullish_support: float
    bearish_support: float
    bullish_structure: float
    bearish_structure: float
    direction: Direction
    directional_lead: float
    contradictory_highs: bool
    contradictory_lows: bool
    bos_conflict: bool
    choch_opposes_trend: bool
    range_evidence: bool
    correction_context: bool
    continuation_confirmed: bool
    reversal_classified: bool


class TrendExpert:
    """Evaluate trend and structure facts into one immutable ExpertOpinion."""

    name = "trend"

    def __init__(self, policy: Optional[TrendExpertPolicy] = None) -> None:
        if policy is not None and not isinstance(policy, TrendExpertPolicy):
            raise TypeError("policy must be a TrendExpertPolicy")
        self._policy = policy or TrendExpertPolicy()

    @property
    def policy(self) -> TrendExpertPolicy:
        return self._policy

    def evaluate(
        self,
        trend: TrendObservation,
        structure: StructureObservation,
        *,
        timestamp: Optional[datetime] = None,
    ) -> ExpertOpinion:
        self._validate_inputs(trend, structure)
        output_timestamp = self._timestamp(timestamp)
        timestamp_delta = abs((trend.observed_at - structure.observed_at).total_seconds())

        bullish_support, bearish_support = self._direction_support(trend, structure)
        direction = self._direction(bullish_support, bearish_support)
        directional_lead = bullish_support - bearish_support
        bullish_structure, bearish_structure = self._structure_support(trend, structure)

        contradictory_highs = trend.higher_high and trend.lower_high
        contradictory_lows = trend.higher_low and trend.lower_low
        bos_conflict = self._bos_conflict(trend, structure)
        choch_opposes_trend = self._choch_opposes_trend(trend, structure)
        quality = self._quality(trend, structure)

        state, state_details = self._state(
            trend=trend,
            structure=structure,
            direction=direction,
            directional_lead=directional_lead,
            bullish_support=bullish_support,
            bearish_support=bearish_support,
            quality=quality,
            choch_opposes_trend=choch_opposes_trend,
        )
        selected_structure = self._selected_structure_support(
            direction, bullish_structure, bearish_structure
        )
        evidence = _Evidence(
            bullish_support=bullish_support,
            bearish_support=bearish_support,
            bullish_structure=bullish_structure,
            bearish_structure=bearish_structure,
            direction=direction,
            directional_lead=directional_lead,
            contradictory_highs=contradictory_highs,
            contradictory_lows=contradictory_lows,
            bos_conflict=bos_conflict,
            choch_opposes_trend=choch_opposes_trend,
            range_evidence=state_details["range_evidence"],
            correction_context=state_details["correction_context"],
            continuation_confirmed=state_details["continuation_confirmed"],
            reversal_classified=state_details["reversal_classified"],
        )

        score = self._score(
            trend=trend,
            direction=direction,
            directional_lead=directional_lead,
            bullish_support=bullish_support,
            bearish_support=bearish_support,
            structure_support=selected_structure,
        )
        confidence = self._confidence(
            trend=trend,
            structure=structure,
            evidence=evidence,
            state=state,
            quality=quality,
            structure_support=selected_structure,
            timestamp_delta=timestamp_delta,
        )
        reasons = self._reasons(trend, structure, evidence, state)
        warnings = self._warnings(
            trend=trend,
            structure=structure,
            evidence=evidence,
            state=state,
            quality=quality,
            structure_support=selected_structure,
            timestamp_delta=timestamp_delta,
        )
        metadata = {
            "supported_observation_versions": self._policy.supported_versions,
            "timeframe": trend.timeframe,
            "bullish_support": self._metric(bullish_support),
            "bearish_support": self._metric(bearish_support),
            "directional_lead": self._metric_signed(directional_lead),
            "structure_support": self._metric(selected_structure),
            "timestamp_delta_seconds": round(timestamp_delta, 6),
            "trend_observation_id": trend.observation_id,
            "structure_observation_id": structure.observation_id,
            "policy_version": self._policy.policy_version,
            "classification_details": {
                "range_evidence": evidence.range_evidence,
                "correction_context": evidence.correction_context,
                "continuation_confirmed": evidence.continuation_confirmed,
                "reversal_classified": evidence.reversal_classified,
                "choch_opposes_trend": evidence.choch_opposes_trend,
                "contradictory_highs": evidence.contradictory_highs,
                "contradictory_lows": evidence.contradictory_lows,
                "bos_conflict": evidence.bos_conflict,
            },
        }

        return ExpertOpinion(
            expert_name=self.name,
            direction=direction,
            state=state.value,
            score=self._metric(score),
            confidence=self._metric(confidence),
            quality=self._metric(quality),
            reasons=reasons,
            warnings=warnings,
            metadata=metadata,
            timestamp=output_timestamp,
        )

    def _validate_inputs(
        self, trend: TrendObservation, structure: StructureObservation
    ) -> None:
        if type(trend) is not TrendObservation:
            raise TypeError("trend must be exactly a TrendObservation")
        if type(structure) is not StructureObservation:
            raise TypeError("structure must be exactly a StructureObservation")
        if trend.version not in self._policy.supported_versions:
            raise ValueError(
                f"unsupported TrendObservation version {trend.version}; "
                "Phase 1 supports version 1"
            )
        if structure.version not in self._policy.supported_versions:
            raise ValueError(
                f"unsupported StructureObservation version {structure.version}; "
                "Phase 1 supports version 1"
            )
        if trend.asset != structure.asset:
            raise ValueError("trend and structure observations must use the same asset")
        if trend.timeframe != structure.timeframe:
            raise ValueError("trend and structure observations must use the same timeframe")

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
    def _direction_support(
        trend: TrendObservation, structure: StructureObservation
    ) -> Tuple[float, float]:
        bullish = 0.0
        bearish = 0.0

        if trend.trend_bias is TrendBias.BULLISH:
            bullish += 25.0
        elif trend.trend_bias is TrendBias.BEARISH:
            bearish += 25.0

        if trend.moving_average_alignment is TrendBias.BULLISH:
            bullish += 15.0
        elif trend.moving_average_alignment is TrendBias.BEARISH:
            bearish += 15.0

        bullish += 12.0 if trend.higher_high else 0.0
        bullish += 12.0 if trend.higher_low else 0.0
        bearish += 12.0 if trend.lower_high else 0.0
        bearish += 12.0 if trend.lower_low else 0.0

        if trend.slope > 0.0:
            bullish += min(trend.slope * 10.0, 10.0)
        elif trend.slope < 0.0:
            bearish += min(abs(trend.slope) * 10.0, 10.0)

        if trend.price_change_pct > 0.0:
            bullish += min(trend.price_change_pct, 8.0)
        elif trend.price_change_pct < 0.0:
            bearish += min(abs(trend.price_change_pct), 8.0)

        if structure.structure_break is StructureBreak.BULLISH_BOS:
            bullish += 20.0
        elif structure.structure_break is StructureBreak.BEARISH_BOS:
            bearish += 20.0
        elif structure.structure_break is StructureBreak.BULLISH_CHOCH:
            bullish += 12.0
        elif structure.structure_break is StructureBreak.BEARISH_CHOCH:
            bearish += 12.0

        if structure.higher_timeframe_bias is TrendBias.BULLISH:
            bullish += 15.0
        elif structure.higher_timeframe_bias is TrendBias.BEARISH:
            bearish += 15.0

        return (
            100.0 * bullish / _MAX_DIRECTION_RAW,
            100.0 * bearish / _MAX_DIRECTION_RAW,
        )

    def _direction(self, bullish: float, bearish: float) -> Direction:
        lead = bullish - bearish
        if lead >= self._policy.direction_lead_threshold:
            return Direction.BULLISH
        if lead <= -self._policy.direction_lead_threshold:
            return Direction.BEARISH
        return Direction.NEUTRAL

    @staticmethod
    def _structure_support(
        trend: TrendObservation, structure: StructureObservation
    ) -> Tuple[float, float]:
        bullish = (25.0 if trend.higher_high else 0.0) + (
            25.0 if trend.higher_low else 0.0
        )
        bearish = (25.0 if trend.lower_high else 0.0) + (
            25.0 if trend.lower_low else 0.0
        )
        if structure.structure_break is StructureBreak.BULLISH_BOS:
            bullish += 50.0
        elif structure.structure_break is StructureBreak.BEARISH_BOS:
            bearish += 50.0
        elif structure.structure_break is StructureBreak.BULLISH_CHOCH:
            bullish += 30.0
        elif structure.structure_break is StructureBreak.BEARISH_CHOCH:
            bearish += 30.0
        return min(bullish, 100.0), min(bearish, 100.0)

    @staticmethod
    def _selected_structure_support(
        direction: Direction, bullish: float, bearish: float
    ) -> float:
        if direction is Direction.BULLISH:
            return bullish
        if direction is Direction.BEARISH:
            return bearish
        return max(bullish, bearish)

    @staticmethod
    def _bos_conflict(
        trend: TrendObservation, structure: StructureObservation
    ) -> bool:
        return (
            trend.trend_bias is TrendBias.BULLISH
            and structure.structure_break is StructureBreak.BEARISH_BOS
        ) or (
            trend.trend_bias is TrendBias.BEARISH
            and structure.structure_break is StructureBreak.BULLISH_BOS
        )

    @staticmethod
    def _choch_opposes_trend(
        trend: TrendObservation, structure: StructureObservation
    ) -> bool:
        return (
            trend.trend_bias is TrendBias.BULLISH
            and structure.structure_break is StructureBreak.BEARISH_CHOCH
        ) or (
            trend.trend_bias is TrendBias.BEARISH
            and structure.structure_break is StructureBreak.BULLISH_CHOCH
        )

    def _state(
        self,
        *,
        trend: TrendObservation,
        structure: StructureObservation,
        direction: Direction,
        directional_lead: float,
        bullish_support: float,
        bearish_support: float,
        quality: float,
        choch_opposes_trend: bool,
    ) -> Tuple[TrendState, Mapping[str, bool]]:
        htf = structure.higher_timeframe_bias
        trend_bias = trend.trend_bias
        ma = trend.moving_average_alignment

        opposite_direction = None
        opposing_support = 0.0
        if trend_bias is TrendBias.BULLISH:
            opposite_direction = Direction.BEARISH
            opposing_support = bearish_support
        elif trend_bias is TrendBias.BEARISH:
            opposite_direction = Direction.BULLISH
            opposing_support = bullish_support

        reversal_classified = (
            choch_opposes_trend
            and opposite_direction is not None
            and direction is opposite_direction
            and opposing_support >= self._policy.reversal_support_threshold
        )

        htf_sign = 1 if htf is TrendBias.BULLISH else -1 if htf is TrendBias.BEARISH else 0
        opposing_short_signals = 0
        if htf_sign:
            if (htf_sign > 0 and trend_bias is TrendBias.BEARISH) or (
                htf_sign < 0 and trend_bias is TrendBias.BULLISH
            ):
                opposing_short_signals += 1
            if (htf_sign > 0 and ma is TrendBias.BEARISH) or (
                htf_sign < 0 and ma is TrendBias.BULLISH
            ):
                opposing_short_signals += 1
            if trend.slope * htf_sign < 0.0:
                opposing_short_signals += 1
            if trend.price_change_pct * htf_sign < 0.0:
                opposing_short_signals += 1
        opposing_bos = (
            htf is TrendBias.BULLISH
            and structure.structure_break is StructureBreak.BEARISH_BOS
        ) or (
            htf is TrendBias.BEARISH
            and structure.structure_break is StructureBreak.BULLISH_BOS
        )
        correction_context = bool(
            htf_sign and opposing_short_signals >= 2 and not opposing_bos
        )

        aligned_directional = (
            trend_bias in (TrendBias.BULLISH, TrendBias.BEARISH)
            and trend_bias is htf
            and trend_bias is ma
        )
        continuation_structure = (
            trend_bias is TrendBias.BULLISH
            and (
                structure.structure_break is StructureBreak.BULLISH_BOS
                or (trend.higher_high and trend.higher_low)
            )
        ) or (
            trend_bias is TrendBias.BEARISH
            and (
                structure.structure_break is StructureBreak.BEARISH_BOS
                or (trend.lower_high and trend.lower_low)
            )
        )
        continuation_confirmed = bool(
            aligned_directional and continuation_structure and not choch_opposes_trend
        )

        range_defined = (
            structure.range_low is not None
            and structure.range_high is not None
            and structure.current_price is not None
        )
        price_inside_range = bool(
            range_defined
            and structure.range_low <= structure.current_price <= structure.range_high
        )
        weak_motion = (
            abs(trend.slope) <= self._policy.weak_slope_threshold
            and abs(trend.price_change_pct) <= self._policy.weak_price_change_threshold
        )
        balanced_flags = (int(trend.higher_high) + int(trend.higher_low)) == (
            int(trend.lower_high) + int(trend.lower_low)
        )
        near_range = price_inside_range or (
            abs(trend.distance_from_range_pct)
            <= self._policy.weak_price_change_threshold
        )
        range_evidence = bool(
            structure.structure_break is StructureBreak.NONE
            and weak_motion
            and near_range
            and balanced_flags
            and (
                trend_bias is TrendBias.NEUTRAL
                or direction is Direction.NEUTRAL
                or abs(directional_lead) < self._policy.direction_lead_threshold
            )
        )

        if quality < self._policy.low_quality_threshold:
            state = TrendState.UNKNOWN
        elif reversal_classified:
            state = TrendState.REVERSAL
        elif correction_context:
            state = TrendState.CORRECTION
        elif continuation_confirmed:
            state = TrendState.TREND
        elif range_evidence:
            state = TrendState.RANGE
        else:
            state = TrendState.UNKNOWN

        return state, {
            "range_evidence": range_evidence,
            "correction_context": correction_context,
            "continuation_confirmed": continuation_confirmed,
            "reversal_classified": reversal_classified,
        }

    @staticmethod
    def _quality(trend: TrendObservation, structure: StructureObservation) -> float:
        return 0.60 * trend.quality + 0.40 * structure.quality

    @staticmethod
    def _score(
        *,
        trend: TrendObservation,
        direction: Direction,
        directional_lead: float,
        bullish_support: float,
        bearish_support: float,
        structure_support: float,
    ) -> float:
        if direction is Direction.NEUTRAL:
            evidence_strength = 100.0 - min(abs(directional_lead), 100.0)
        else:
            evidence_strength = max(bullish_support, bearish_support)
        return (
            0.45 * evidence_strength
            + 0.30 * trend.trend_strength
            + 0.25 * structure_support
        )

    def _confidence(
        self,
        *,
        trend: TrendObservation,
        structure: StructureObservation,
        evidence: _Evidence,
        state: TrendState,
        quality: float,
        structure_support: float,
        timestamp_delta: float,
    ) -> float:
        if evidence.direction is Direction.NEUTRAL:
            agreement = 100.0 - min(abs(evidence.directional_lead), 100.0)
        else:
            selected_bias = (
                TrendBias.BULLISH
                if evidence.direction is Direction.BULLISH
                else TrendBias.BEARISH
            )
            aligned = sum(
                value is selected_bias
                for value in (
                    trend.trend_bias,
                    trend.moving_average_alignment,
                    structure.higher_timeframe_bias,
                )
            )
            agreement = (
                0.55 * min(abs(evidence.directional_lead), 100.0)
                + 0.45 * (aligned / 3.0 * 100.0)
            )

        confidence_quality = 0.50 * quality + 0.50 * min(
            trend.quality, structure.quality
        )
        base_structure_clarity = structure_support
        if state is TrendState.RANGE and structure.structure_break is StructureBreak.NONE:
            base_structure_clarity = 80.0 if evidence.range_evidence else 60.0
        structure_clarity = (
            0.70 * base_structure_clarity + 0.30 * structure.structure_quality
        )
        if evidence.contradictory_highs:
            structure_clarity -= 25.0
        if evidence.contradictory_lows:
            structure_clarity -= 25.0
        if evidence.bos_conflict:
            structure_clarity -= 20.0
        structure_clarity = max(structure_clarity, 0.0)

        tolerance = self._policy.timestamp_tolerance_seconds
        if timestamp_delta <= tolerance:
            timestamp_coherence = 100.0
        else:
            timestamp_coherence = max(
                0.0,
                100.0
                - 100.0 * (timestamp_delta - tolerance) / max(tolerance, 1.0),
            )

        confidence = (
            0.35 * agreement
            + 0.30 * confidence_quality
            + 0.25 * structure_clarity
            + 0.10 * timestamp_coherence
        )
        if quality < self._policy.low_quality_threshold:
            confidence = min(confidence, quality)
        if state is TrendState.REVERSAL:
            confidence = min(confidence, self._policy.reversal_confidence_cap)
        return confidence

    def _reasons(
        self,
        trend: TrendObservation,
        structure: StructureObservation,
        evidence: _Evidence,
        state: TrendState,
    ) -> Tuple[str, ...]:
        reasons: List[str] = []
        if (
            trend.trend_bias is TrendBias.BULLISH
            and trend.moving_average_alignment is TrendBias.BULLISH
        ):
            reasons.append("Trend bias and moving-average alignment are bullish.")
        elif (
            trend.trend_bias is TrendBias.BEARISH
            and trend.moving_average_alignment is TrendBias.BEARISH
        ):
            reasons.append("Trend bias and moving-average alignment are bearish.")

        if trend.higher_high and trend.higher_low:
            reasons.append("Higher highs and higher lows support bullish structure.")
        if trend.lower_high and trend.lower_low:
            reasons.append("Lower highs and lower lows support bearish structure.")

        if structure.structure_break is StructureBreak.BULLISH_BOS:
            reasons.append("Bullish break of structure supports continuation.")
        elif structure.structure_break is StructureBreak.BEARISH_BOS:
            reasons.append("Bearish break of structure supports continuation.")
        elif structure.structure_break is StructureBreak.BULLISH_CHOCH:
            reasons.append("Bullish change of character affects structure classification.")
        elif structure.structure_break is StructureBreak.BEARISH_CHOCH:
            reasons.append("Bearish change of character affects structure classification.")

        if state is TrendState.CORRECTION:
            reasons.append(
                f"Higher-timeframe bias remains {structure.higher_timeframe_bias.value.lower()} "
                "while short-term evidence opposes it."
            )
        elif state is TrendState.REVERSAL:
            reasons.append(
                "Opposing CHOCH and directional evidence support a developing reversal."
            )
        elif state is TrendState.TREND:
            reasons.append("Aligned trend, structure, and higher-timeframe evidence support TREND.")
        elif state is TrendState.RANGE:
            reasons.append("Balanced directional evidence and weak movement support RANGE.")
        else:
            reasons.append("Available evidence does not support a stable canonical trend state.")

        if evidence.direction is Direction.BULLISH:
            reasons.append("Bullish evidence has a material lead over bearish evidence.")
        elif evidence.direction is Direction.BEARISH:
            reasons.append("Bearish evidence has a material lead over bullish evidence.")
        else:
            reasons.append("Directional evidence remains balanced within the neutral threshold.")
        return self._deduplicate(reasons, self._policy.reason_limit)

    def _warnings(
        self,
        *,
        trend: TrendObservation,
        structure: StructureObservation,
        evidence: _Evidence,
        state: TrendState,
        quality: float,
        structure_support: float,
        timestamp_delta: float,
    ) -> Tuple[str, ...]:
        warnings: List[str] = []
        if quality < self._policy.low_quality_threshold or min(
            trend.quality, structure.quality
        ) < self._policy.low_quality_threshold:
            warnings.append("Input observation quality is below the policy threshold.")
        if abs(trend.quality - structure.quality) >= self._policy.quality_gap_warning_threshold:
            warnings.append("Input observation qualities differ materially.")
        if timestamp_delta > self._policy.timestamp_tolerance_seconds:
            warnings.append("Observation timestamps exceed the policy alignment tolerance.")
        if evidence.contradictory_highs:
            warnings.append("Higher-high and lower-high flags are both present.")
        if evidence.contradictory_lows:
            warnings.append("Higher-low and lower-low flags are both present.")
        if (
            trend.trend_bias in (TrendBias.BULLISH, TrendBias.BEARISH)
            and structure.higher_timeframe_bias
            in (TrendBias.BULLISH, TrendBias.BEARISH)
            and trend.trend_bias is not structure.higher_timeframe_bias
        ):
            warnings.append("Trend bias and higher-timeframe bias are mixed.")
        if abs(evidence.directional_lead) < self._policy.direction_lead_threshold:
            warnings.append("Directional evidence lead is below the policy threshold.")
        if evidence.bos_conflict:
            warnings.append("Break of structure conflicts with the observed trend direction.")
        if evidence.choch_opposes_trend and state is not TrendState.REVERSAL:
            warnings.append("Reversal evidence is developing but remains unconfirmed.")
        if state is TrendState.REVERSAL:
            warnings.append("Reversal classification lacks separate BOS confirmation in Phase 1.")
        if structure_support < self._policy.insufficient_structure_threshold:
            warnings.append("Structure confirmation is insufficient for a strong conclusion.")
        if not _SUPPORTED_TIMEFRAME.fullmatch(trend.timeframe.lower()):
            warnings.append("Timeframe semantics are not recognized by the Phase 1 policy.")
        return self._deduplicate(warnings, self._policy.warning_limit)

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

    @staticmethod
    def _metric_signed(value: float) -> float:
        return round(min(max(value, -100.0), 100.0), 6)
