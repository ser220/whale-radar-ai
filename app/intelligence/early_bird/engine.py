"""Pure deterministic opportunity evaluation and ranking."""

from dataclasses import replace
from datetime import datetime, timezone
import math
from typing import Any, Dict, Iterable, Optional, Tuple

from app.intelligence.early_bird.enums import EarlyBirdFactor
from app.intelligence.early_bird.models import (
    EarlyBirdAssessment,
    EarlyBirdCandidate,
    _percentage,
    _utc_datetime,
)
from app.intelligence.early_bird.policy import EarlyBirdPolicy


_FACTOR_FIELDS = (
    (EarlyBirdFactor.WHALE_ACTIVITY, "whale_activity_score", "whale_activity_weight"),
    (
        EarlyBirdFactor.OPEN_INTEREST_CHANGE,
        "open_interest_change_score",
        "open_interest_change_weight",
    ),
    (
        EarlyBirdFactor.FUNDING_DIVERGENCE,
        "funding_divergence_score",
        "funding_divergence_weight",
    ),
    (
        EarlyBirdFactor.VOLUME_EXPANSION,
        "volume_expansion_score",
        "volume_expansion_weight",
    ),
    (
        EarlyBirdFactor.RELATIVE_STRENGTH,
        "relative_strength_score",
        "relative_strength_weight",
    ),
    (
        EarlyBirdFactor.LIQUIDITY_EVENT,
        "liquidity_event_score",
        "liquidity_event_weight",
    ),
    (
        EarlyBirdFactor.STRUCTURE_EVENT,
        "structure_event_score",
        "structure_event_weight",
    ),
    (
        EarlyBirdFactor.MOMENTUM_SHIFT,
        "momentum_shift_score",
        "momentum_shift_weight",
    ),
)


_FACTOR_REASONS = {
    EarlyBirdFactor.WHALE_ACTIVITY: "Unusual whale activity is a material opportunity factor.",
    EarlyBirdFactor.OPEN_INTEREST_CHANGE: "Open-interest participation is expanding.",
    EarlyBirdFactor.FUNDING_DIVERGENCE: "Funding divergence adds asymmetric market interest.",
    EarlyBirdFactor.VOLUME_EXPANSION: "Trading volume is expanding.",
    EarlyBirdFactor.RELATIVE_STRENGTH: "Relative strength is elevated versus the broader market.",
    EarlyBirdFactor.LIQUIDITY_EVENT: "A liquidity event increases analysis urgency.",
    EarlyBirdFactor.STRUCTURE_EVENT: "Market structure is developing.",
    EarlyBirdFactor.MOMENTUM_SHIFT: "Momentum conditions are shifting.",
}


def _bounded(value: float) -> float:
    return round(min(100.0, max(0.0, value)), 6)


class EarlyBirdEngine:
    """Ranks explainable opportunities without producing a trade conclusion."""

    def __init__(self, policy: Optional[EarlyBirdPolicy] = None) -> None:
        if policy is None:
            policy = EarlyBirdPolicy()
        if not isinstance(policy, EarlyBirdPolicy):
            raise TypeError("policy must be an EarlyBirdPolicy")
        self._policy = policy

    @property
    def policy(self) -> EarlyBirdPolicy:
        return self._policy

    def evaluate_candidate(
        self,
        candidate: EarlyBirdCandidate,
        *,
        timestamp: Optional[datetime] = None,
    ) -> EarlyBirdAssessment:
        if not isinstance(candidate, EarlyBirdCandidate):
            raise TypeError("candidate must be an EarlyBirdCandidate")
        evaluated_at = self._evaluation_time(timestamp)

        contributions = self._factor_contributions(candidate)
        raw_opportunity = sum(
            item["weighted_contribution"] for item in contributions.values()
        )
        reliability_factor = math.sqrt(
            (candidate.quality / 100.0)
            * (candidate.data_completeness_score / 100.0)
        )
        opportunity = _bounded(raw_opportunity * reliability_factor)

        event_urgency = _bounded(
            candidate.whale_activity_score * self._policy.urgency_whale_weight
            + candidate.liquidity_event_score
            * self._policy.urgency_liquidity_weight
            + candidate.structure_event_score
            * self._policy.urgency_structure_weight
        )
        effective_quality = _bounded(
            (candidate.quality + candidate.data_completeness_score) / 2.0
        )
        priority = _bounded(
            opportunity * self._policy.priority_opportunity_weight
            + candidate.freshness_score * self._policy.priority_freshness_weight
            + event_urgency * self._policy.priority_urgency_weight
            + effective_quality * self._policy.priority_data_quality_weight
        )

        age_proxy, overextension = self._age_proxy(candidate)
        maturity = _bounded(
            candidate.structure_event_score
            * self._policy.maturity_structure_weight
            + candidate.momentum_shift_score
            * self._policy.maturity_momentum_weight
            + candidate.volume_expansion_score
            * self._policy.maturity_volume_weight
            + candidate.open_interest_change_score
            * self._policy.maturity_open_interest_weight
            + age_proxy * self._policy.maturity_age_weight
        )

        reasons = self._reasons(candidate, contributions, maturity)
        warnings = self._warnings(candidate, contributions, raw_opportunity, maturity)
        metadata: Dict[str, Any] = {
            "candidate_source": candidate.source,
            "effective_quality": effective_quality,
            "event_urgency": event_urgency,
            "policy_version": self._policy.policy_version,
            "raw_opportunity_score": _bounded(raw_opportunity),
            "reliability_factor": round(reliability_factor, 6),
        }
        if overextension is not None:
            metadata["overextension_score"] = overextension

        return EarlyBirdAssessment(
            assessment_id="early-bird:{0}:v{1}".format(
                candidate.candidate_id, self._policy.policy_version
            ),
            candidate_id=candidate.candidate_id,
            asset=candidate.asset,
            evaluated_at=evaluated_at,
            opportunity_score=opportunity,
            priority_score=priority,
            maturity_score=maturity,
            quality=effective_quality,
            rank=None,
            reasons=reasons,
            warnings=warnings,
            factor_contributions=contributions,
            source_event_ids=candidate.fast_event_ids,
            source_observation_ids=candidate.observation_ids,
            metadata=metadata,
        )

    def rank_candidates(
        self,
        candidates: Iterable[EarlyBirdCandidate],
        *,
        limit: Optional[int] = None,
        timestamp: Optional[datetime] = None,
    ) -> Tuple[EarlyBirdAssessment, ...]:
        result_limit = self._result_limit(limit)
        if isinstance(candidates, (str, bytes)):
            raise TypeError("candidates must be an iterable of EarlyBirdCandidate")
        try:
            candidate_values = tuple(candidates)
        except TypeError as exc:
            raise TypeError(
                "candidates must be an iterable of EarlyBirdCandidate"
            ) from exc

        seen_ids = set()
        for candidate in candidate_values:
            if not isinstance(candidate, EarlyBirdCandidate):
                raise TypeError("candidates must contain only EarlyBirdCandidate values")
            if candidate.candidate_id in seen_ids:
                raise ValueError(
                    "duplicate candidate_id: {0}".format(candidate.candidate_id)
                )
            seen_ids.add(candidate.candidate_id)

        if not candidate_values:
            return ()

        evaluated_at = self._evaluation_time(timestamp)
        assessments = tuple(
            self.evaluate_candidate(candidate, timestamp=evaluated_at)
            for candidate in candidate_values
        )
        ordered = sorted(
            assessments,
            key=lambda item: (
                -item.priority_score,
                -item.opportunity_score,
                item.maturity_score,
                item.asset,
                item.candidate_id,
            ),
        )
        selected = ordered[:result_limit]
        return tuple(
            replace(assessment, rank=index)
            for index, assessment in enumerate(selected, start=1)
        )

    def _evaluation_time(self, timestamp: Optional[datetime]) -> datetime:
        if timestamp is None:
            return datetime.now(timezone.utc)
        return _utc_datetime(timestamp, "timestamp")

    def _result_limit(self, limit: Optional[int]) -> int:
        if limit is None:
            return self._policy.maximum_results
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer")
        if limit < 1:
            raise ValueError("limit must be at least 1")
        return min(limit, self._policy.maximum_results)

    def _factor_contributions(
        self, candidate: EarlyBirdCandidate
    ) -> Dict[str, Dict[str, float]]:
        contributions: Dict[str, Dict[str, float]] = {}
        for factor, score_field, weight_field in _FACTOR_FIELDS:
            score = getattr(candidate, score_field)
            weight = getattr(self._policy, weight_field)
            contributions[factor.value] = {
                "score": score,
                "weight": weight,
                "weighted_contribution": _bounded(score * weight),
            }
        return contributions

    def _age_proxy(
        self, candidate: EarlyBirdCandidate
    ) -> Tuple[float, Optional[float]]:
        freshness_age = 100.0 - candidate.freshness_score
        if "overextension_score" not in candidate.metadata:
            return freshness_age, None
        overextension = _percentage(
            candidate.metadata["overextension_score"], "overextension_score"
        )
        return (freshness_age + overextension) / 2.0, overextension

    def _reasons(
        self,
        candidate: EarlyBirdCandidate,
        contributions: Dict[str, Dict[str, float]],
        maturity: float,
    ) -> Tuple[str, ...]:
        eligible = []
        for factor, score_field, _ in _FACTOR_FIELDS:
            if getattr(candidate, score_field) >= self._policy.material_factor_threshold:
                eligible.append(
                    (factor, contributions[factor.value]["weighted_contribution"])
                )
        eligible.sort(key=lambda item: (-item[1], item[0].value))

        reasons = []
        for index, (factor, _) in enumerate(eligible):
            if index == 0 and factor is EarlyBirdFactor.WHALE_ACTIVITY:
                reason = "Unusual whale activity is the strongest opportunity factor."
            else:
                reason = _FACTOR_REASONS[factor]
            if reason not in reasons:
                reasons.append(reason)

        if (
            maturity < self._policy.material_factor_threshold
            and candidate.structure_event_score
            < self._policy.material_factor_threshold
        ):
            reasons.append(
                "The situation remains early because structure confirmation is limited."
            )
        if not reasons:
            reasons.append("No individual opportunity factor is materially elevated.")
        return tuple(reasons[: self._policy.reason_limit])

    def _warnings(
        self,
        candidate: EarlyBirdCandidate,
        contributions: Dict[str, Dict[str, float]],
        raw_opportunity: float,
        maturity: float,
    ) -> Tuple[str, ...]:
        warnings = []
        if candidate.quality < self._policy.minimum_quality_threshold:
            warnings.append("Candidate data quality is below the policy threshold.")
        if (
            candidate.data_completeness_score
            < self._policy.minimum_completeness_threshold
        ):
            warnings.append("Candidate data is incomplete.")
        if candidate.freshness_score < self._policy.stale_freshness_threshold:
            warnings.append("Candidate event is stale.")
        if maturity >= self._policy.over_mature_threshold:
            warnings.append("The opportunity appears over-mature for early attention.")

        weighted_values = tuple(
            item["weighted_contribution"] for item in contributions.values()
        )
        if raw_opportunity > 0.0:
            dominant_share = max(weighted_values) / raw_opportunity
            if dominant_share >= self._policy.dominant_factor_share_threshold:
                warnings.append("Opportunity is driven almost entirely by one factor.")
        if candidate.whale_activity_score == 0.0:
            warnings.append("No whale activity is present in this whale-first assessment.")

        independent_count = sum(
            1
            for _, score_field, _ in _FACTOR_FIELDS
            if getattr(candidate, score_field)
            >= self._policy.independent_factor_threshold
        )
        if independent_count < self._policy.minimum_independent_factors:
            warnings.append("Insufficient independent opportunity factors are present.")
        return tuple(warnings[: self._policy.warning_limit])
