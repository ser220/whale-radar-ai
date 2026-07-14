"""Pure adapter from v20 legacy intelligence output to ExpertOpinion."""

from collections.abc import Mapping
from datetime import datetime, timezone
import math
from numbers import Real
from typing import Any, Dict, List, Optional, Tuple

from app.intelligence.contracts import Direction, ExpertOpinion, TrendState


class LegacyIntelligenceAdapter:
    """Represent an already-produced v20 intelligence result as one opinion.

    The adapter does not run legacy engines. It only consumes their aggregate
    output, preserves source provenance, and normalizes it into the common
    ExpertOpinion contract. The legacy result remains an opinion rather than a
    market-state or trade decision.
    """

    EXPERT_NAME = "legacy_intelligence"

    _EVIDENCE_KEYS = (
        "source_consensus",
        "campaign",
        "event_memory",
        "similar_events",
        "wallet_memory",
        "wallet_behaviour",
        "pressure",
        "context",
        "exchange_context",
    )

    def __init__(self, legacy_version: str = "v20") -> None:
        normalized_version = str(legacy_version or "").strip()
        if not normalized_version:
            raise ValueError("legacy_version cannot be empty")
        self._legacy_version = normalized_version

    @property
    def legacy_version(self) -> str:
        return self._legacy_version

    def adapt(
        self,
        legacy_output: Mapping,
        *,
        timestamp: Optional[datetime] = None,
    ) -> ExpertOpinion:
        """Convert one aggregate legacy result without invoking legacy code."""
        if not isinstance(legacy_output, Mapping):
            raise TypeError("legacy_output must be a mapping")

        payload = dict(legacy_output)
        resolved_timestamp = self._timestamp(payload, timestamp)
        warnings: List[str] = []

        probability = self._mapping(payload.get("probability_raw"))
        ai_decision = self._mapping(payload.get("ai_decision_raw"))
        market_regime = self._mapping(payload.get("market_regime_raw"))
        meta_decision = self._mapping(payload.get("meta_decision_raw"))
        self_confidence = self._mapping(payload.get("self_confidence_raw"))

        bullish = self._percentage(
            probability.get("bullish"), "probability_raw.bullish", warnings
        )
        bearish = self._percentage(
            probability.get("bearish"), "probability_raw.bearish", warnings
        )

        direction = self._direction(
            payload=payload,
            bullish=bullish,
            bearish=bearish,
            market_regime=market_regime,
            warnings=warnings,
        )
        state = self._state(payload, probability, market_regime, warnings)

        ai_confidence = self._percentage(
            ai_decision.get("overall_confidence"),
            "ai_decision_raw.overall_confidence",
            warnings,
        )
        self_trust = self._percentage(
            self_confidence.get("score"), "self_confidence_raw.score", warnings
        )
        meta_score = self._percentage(
            meta_decision.get("final"), "meta_decision_raw.final", warnings
        )

        probability_score = self._probability_score(bullish, bearish)
        confidence = self._first(
            self_trust,
            ai_confidence,
            meta_score,
            probability_score,
        )
        if confidence is None:
            confidence = 0.0
            warnings.append("Legacy confidence was unavailable; 0.0 was used.")

        score = self._first(meta_score, probability_score, ai_confidence, self_trust)
        if score is None:
            score = 0.0
            warnings.append("Legacy opinion score was unavailable; 0.0 was used.")

        evidence_references = self._evidence_references(payload)
        quality, quality_basis = self._quality(
            payload=payload,
            probability_complete=(bullish is not None and bearish is not None),
            ai_decision=ai_decision,
            market_regime=market_regime,
            evidence_references=evidence_references,
            warnings=warnings,
        )
        reasons = self._reasons(
            payload=payload,
            ai_decision=ai_decision,
            market_regime=market_regime,
            bullish=bullish,
            bearish=bearish,
        )
        if not reasons:
            warnings.append("Legacy reasoning was unavailable.")

        invalidations = self._strings(ai_decision.get("invalidates"))
        warnings.extend(
            "Legacy invalidation: {0}".format(item) for item in invalidations
        )

        recommendation = self._text(ai_decision.get("best_action"))
        if recommendation is None:
            recommendation = self._text(payload.get("action"))

        risk = self._text(market_regime.get("risk"))
        source_modules = self._source_modules(payload)

        metadata: Dict[str, Any] = {
            "legacy_version": self._legacy_version,
            "source_modules": source_modules,
            "generated_at": resolved_timestamp.isoformat(),
            "recommendation": recommendation,
            "risk": risk,
            "evidence_references": evidence_references,
            "quality_basis": quality_basis,
            "probability": {
                "bullish": bullish,
                "bearish": bearish,
            },
        }

        return ExpertOpinion(
            expert_name=self.EXPERT_NAME,
            direction=direction,
            state=state.value,
            score=score,
            confidence=confidence,
            quality=quality,
            reasons=reasons,
            warnings=self._deduplicate(warnings),
            metadata=metadata,
            timestamp=resolved_timestamp,
        )

    @staticmethod
    def _mapping(value: Any) -> Dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        return {}

    @staticmethod
    def _text(value: Any) -> Optional[str]:
        if not isinstance(value, str):
            return None
        normalized = " ".join(value.split())
        return normalized or None

    @classmethod
    def _strings(cls, value: Any) -> Tuple[str, ...]:
        if isinstance(value, str) or not isinstance(value, (list, tuple)):
            return ()
        normalized: List[str] = []
        for item in value:
            text = cls._text(item)
            if text is not None and text not in normalized:
                normalized.append(text)
        return tuple(normalized)

    @staticmethod
    def _timestamp(payload: Mapping, value: Optional[datetime]) -> datetime:
        candidate: Any = value
        if candidate is None:
            candidate = payload.get("generated_at") or payload.get("timestamp")
        if candidate is None:
            return datetime.now(timezone.utc)
        if isinstance(candidate, str):
            text = candidate.strip()
            if not text:
                raise ValueError("timestamp cannot be empty")
            try:
                candidate = datetime.fromisoformat(text.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("timestamp must be an ISO-8601 datetime") from exc
        if not isinstance(candidate, datetime):
            raise TypeError("timestamp must be a datetime or ISO-8601 string")
        if candidate.tzinfo is None or candidate.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return candidate.astimezone(timezone.utc)

    @staticmethod
    def _percentage(
        value: Any,
        field_name: str,
        warnings: List[str],
    ) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, bool):
            warnings.append("{0} was not numeric and was ignored.".format(field_name))
            return None
        if isinstance(value, Real):
            normalized = float(value)
        elif isinstance(value, str):
            try:
                normalized = float(value.strip())
            except ValueError:
                warnings.append("{0} was not numeric and was ignored.".format(field_name))
                return None
        else:
            warnings.append("{0} was not numeric and was ignored.".format(field_name))
            return None
        if not math.isfinite(normalized):
            warnings.append("{0} was not finite and was ignored.".format(field_name))
            return None
        bounded = max(0.0, min(normalized, 100.0))
        if bounded != normalized:
            warnings.append(
                "{0} was clamped to the 0-100 range.".format(field_name)
            )
        return bounded

    @classmethod
    def _explicit_direction(
        cls,
        value: Any,
    ) -> Optional[Direction]:
        text = cls._text(value)
        if text is None:
            return None
        normalized = text.upper().replace("-", "_").replace(" ", "_")
        if normalized in {"BULLISH", "LONG", "BULLISH_CONTINUATION"}:
            return Direction.BULLISH
        if normalized in {"BEARISH", "SHORT", "BEARISH_CONTINUATION"}:
            return Direction.BEARISH
        if normalized in {"NEUTRAL", "WAIT", "UNKNOWN"}:
            return Direction.NEUTRAL
        return None

    @classmethod
    def _direction(
        cls,
        *,
        payload: Mapping,
        bullish: Optional[float],
        bearish: Optional[float],
        market_regime: Mapping,
        warnings: List[str],
    ) -> Direction:
        explicit_value = payload.get("direction")
        explicit = cls._explicit_direction(explicit_value)
        if explicit is not None:
            return explicit
        if explicit_value is not None:
            warnings.append("Legacy direction was unrecognized and was ignored.")

        if bullish is not None and bearish is not None:
            if bullish > bearish:
                return Direction.BULLISH
            if bearish > bullish:
                return Direction.BEARISH
            return Direction.NEUTRAL

        regime = cls._text(market_regime.get("regime"))
        if regime is not None:
            normalized_regime = regime.lower()
            if "accumulation" in normalized_regime:
                return Direction.BULLISH
            if "distribution" in normalized_regime:
                return Direction.BEARISH

        warnings.append("Legacy direction was unavailable; NEUTRAL was used.")
        return Direction.NEUTRAL

    @classmethod
    def _state(
        cls,
        payload: Mapping,
        probability: Mapping,
        market_regime: Mapping,
        warnings: List[str],
    ) -> TrendState:
        explicit = cls._text(payload.get("state"))
        if explicit is not None:
            try:
                return TrendState(explicit.upper())
            except ValueError:
                warnings.append("Legacy state was unrecognized and was ignored.")

        regime = cls._text(market_regime.get("regime"))
        if regime is not None:
            normalized = regime.lower()
            if "reversal" in normalized:
                return TrendState.REVERSAL
            if "correction" in normalized:
                return TrendState.CORRECTION
            if "range" in normalized or "sideways" in normalized:
                return TrendState.RANGE
            if "accumulation" in normalized or "distribution" in normalized:
                return TrendState.TREND

        bias = cls._text(probability.get("bias"))
        if bias is not None and "continuation" in bias.lower():
            return TrendState.TREND

        warnings.append("Legacy state was unavailable; UNKNOWN was used.")
        return TrendState.UNKNOWN

    @staticmethod
    def _probability_score(
        bullish: Optional[float],
        bearish: Optional[float],
    ) -> Optional[float]:
        values = [value for value in (bullish, bearish) if value is not None]
        return max(values) if values else None

    @staticmethod
    def _first(*values: Optional[float]) -> Optional[float]:
        for value in values:
            if value is not None:
                return value
        return None

    @classmethod
    def _evidence_references(cls, payload: Mapping) -> Tuple[str, ...]:
        return tuple(
            key
            for key in cls._EVIDENCE_KEYS
            if cls._text(payload.get(key)) is not None
        )

    @classmethod
    def _quality(
        cls,
        *,
        payload: Mapping,
        probability_complete: bool,
        ai_decision: Mapping,
        market_regime: Mapping,
        evidence_references: Tuple[str, ...],
        warnings: List[str],
    ) -> Tuple[float, str]:
        explicit = cls._percentage(payload.get("quality"), "quality", warnings)
        if explicit is not None:
            return explicit, "legacy_output.quality"

        snapshot_quality = cls._mapping(payload.get("snapshot_quality"))
        explicit = cls._percentage(
            snapshot_quality.get("overall"), "snapshot_quality.overall", warnings
        )
        if explicit is not None:
            return explicit, "snapshot_quality.overall"

        checks = (
            probability_complete,
            bool(ai_decision),
            bool(market_regime),
            cls._text(payload.get("summary")) is not None,
            bool(evidence_references),
        )
        return sum(20.0 for value in checks if value), "recognized_field_completeness"

    @classmethod
    def _reasons(
        cls,
        *,
        payload: Mapping,
        ai_decision: Mapping,
        market_regime: Mapping,
        bullish: Optional[float],
        bearish: Optional[float],
    ) -> Tuple[str, ...]:
        candidates: List[Optional[str]] = [
            cls._text(payload.get("summary")),
            cls._text(ai_decision.get("summary")),
            cls._text(market_regime.get("message")),
        ]
        if bullish is not None and bearish is not None:
            candidates.append(
                "Legacy probability: BULLISH {0:.2f}%, BEARISH {1:.2f}%.".format(
                    bullish, bearish
                )
            )
        recommendation = cls._text(ai_decision.get("best_action"))
        if recommendation is None:
            recommendation = cls._text(payload.get("action"))
        if recommendation is not None:
            candidates.append("Legacy recommendation: {0}".format(recommendation))

        reasons: List[str] = []
        for candidate in candidates:
            if candidate is not None and candidate not in reasons:
                reasons.append(candidate)
        return tuple(reasons)

    @staticmethod
    def _source_modules(payload: Mapping) -> Tuple[str, ...]:
        modules: List[str] = ["app.engine.intelligence"]
        sources = (
            ("probability_raw", "app.engine.probability_engine"),
            ("ai_decision_raw", "app.engine.decision_engine"),
            ("market_regime_raw", "app.engine.market_regime"),
            ("meta_decision_raw", "app.engine.meta_decision"),
            ("self_confidence_raw", "app.engine.self_confidence"),
            ("pattern_confidence_raw", "app.engine.pattern_confidence"),
            ("source_consensus", "app.engine.source_consensus"),
            ("campaign", "app.engine.campaign_detector"),
            ("event_memory", "app.engine.event_memory"),
            ("wallet_memory", "app.engine.wallet_memory"),
            ("wallet_behaviour", "app.engine.wallet_behaviour"),
        )
        for field_name, module_name in sources:
            if payload.get(field_name) not in (None, "", (), [], {}):
                modules.append(module_name)
        return tuple(modules)

    @staticmethod
    def _deduplicate(values: List[str]) -> Tuple[str, ...]:
        result: List[str] = []
        for value in values:
            if value not in result:
                result.append(value)
        return tuple(result)
