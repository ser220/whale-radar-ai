from typing import Any, Dict, List, Optional

from app.decision.trade_decision import TradeDecision


class TradeReadinessEngine:
    """
    Converts DecisionEngineV2 output and SnapshotQuality
    into the canonical TradeDecision used by Telegram.

    Alpha safety rules:
    - ACTION requires at least three directional sources;
    - ACTION requires spot confirmation;
    - missing core confirmation limits readiness;
    - this engine does not execute trades.
    """

    def build(
        self,
        decision: Dict[str, Any],
        snapshot_quality: Dict[str, Any],
        snapshot_id: Optional[str] = None,
    ) -> TradeDecision:
        direction = str(
            decision.get("direction") or "neutral"
        ).lower()

        confidence = self._bounded(
            decision.get("confidence")
        )

        institutional_score = self._bounded(
            decision.get("institutional_score")
        )

        evidence = decision.get("evidence") or []
        conflicts = decision.get("conflicts") or []

        active_sources = set(
            decision.get("active_sources") or []
        )

        if not active_sources:
            active_sources = {
                str(row.get("source") or "").lower()
                for row in evidence
                if row.get("source")
            }

        directional_sources = set(
            decision.get("directional_sources") or []
        )

        if not directional_sources:
            directional_sources = {
                str(row.get("source") or "").lower()
                for row in evidence
                if row.get("direction")
                in {
                    "bullish",
                    "bearish",
                }
                and row.get("source")
            }

        missing = list(
            decision.get("missing_confirmations") or []
        )

        if not missing:
            missing = self._derive_missing_confirmations(
                active_sources=active_sources,
                evidence=evidence,
            )

        quality = self._bounded(
            snapshot_quality.get("overall")
        )

        # Alpha confidence cannot exceed the completeness
        # of the synchronized market snapshot.
        confidence = min(
            confidence,
            max(
                quality,
                45.0,
            ),
        )

        support_ratio = self._support_ratio(
            evidence=evidence,
            direction=direction,
        )

        stability = self._stability(
            support_ratio=support_ratio,
            source_count=len(directional_sources),
            conflicts=len(conflicts),
        )

        readiness = self._readiness(
            confidence=confidence,
            institutional_score=institutional_score,
            quality=quality,
            stability=stability,
            conflicts=len(conflicts),
        )

        has_spot = bool(
            {
                "spot",
                "spot_cvd",
                "spot_echo",
            }
            & active_sources
        )

        has_price_delta = (
            "price_delta" in active_sources
            and any(
                row.get("fact_type")
                in {
                    "price_rising",
                    "price_falling",
                    "breakout",
                    "breakdown",
                }
                for row in evidence
            )
        )

        has_oi_delta = (
            "oi_delta" in active_sources
        )

        readiness = self._apply_safety_caps(
            readiness=readiness,
            has_spot=has_spot,
            has_price_delta=has_price_delta,
            has_oi_delta=has_oi_delta,
            directional_source_count=len(
                directional_sources
            ),
        )

        status = self._status(
            readiness
        )

        bias = {
            "bullish": "LONG",
            "bearish": "SHORT",
        }.get(
            direction,
            "NEUTRAL",
        )

        risk = str(
            decision.get("risk") or "UNKNOWN"
        ).upper()

        large_whale_event = any(
            str(row.get("source") or "").lower()
            == "arkham"
            and float(row.get("value") or 0.0)
            >= 20_000_000
            for row in evidence
        )

        if (
            large_whale_event
            and risk in {
                "UNKNOWN",
                "LOW",
            }
        ):
            risk = "MODERATE"

        velocity = self._velocity(
            readiness=readiness,
            missing_count=len(missing),
            conflicts=len(conflicts),
        )

        eta = self._eta(
            status=status,
            velocity=velocity,
            missing_count=len(missing),
        )

        action = self._action(
            status=status,
            bias=bias,
            has_price_delta=has_price_delta,
        )

        reasons = self._reasons(
            evidence
        )

        return TradeDecision(
            asset=str(
                decision.get("asset") or "UNKNOWN"
            ).upper(),
            status=status,
            bias=bias,
            trade_readiness=round(
                readiness,
                1,
            ),
            confidence=round(
                confidence,
                1,
            ),
            institutional_score=round(
                institutional_score,
                1,
            ),
            hypothesis_stability=round(
                stability,
                1,
            ),
            market_velocity=velocity,
            eta=eta,
            action=action,
            risk=risk,
            execution_window=(
                "OPEN"
                if status == "ACTION"
                else status
            ),
            missing_confirmations=missing,
            reasons=reasons,
        )

    @staticmethod
    def _derive_missing_confirmations(
        active_sources: set,
        evidence: List[Dict[str, Any]],
    ) -> List[str]:
        missing = []

        has_spot = bool(
            {
                "spot",
                "spot_cvd",
                "spot_echo",
            }
            & active_sources
        )

        has_oi_delta = (
            "oi_delta" in active_sources
        )

        has_price_direction = any(
            row.get("fact_type")
            in {
                "price_rising",
                "price_falling",
                "breakout",
                "breakdown",
            }
            for row in evidence
        )

        if not has_spot:
            missing.append(
                "Spot confirmation"
            )

        if not has_oi_delta:
            missing.append(
                "OI direction"
            )

        if not has_price_direction:
            missing.append(
                "Price structure confirmation"
            )

        if "liquidations" not in active_sources:
            missing.append(
                "Liquidation confirmation"
            )

        if "history" not in active_sources:
            missing.append(
                "Historical confirmation"
            )

        if "campaign" not in active_sources:
            missing.append(
                "Campaign confirmation"
            )

        return missing

    @staticmethod
    def _readiness(
        confidence: float,
        institutional_score: float,
        quality: float,
        stability: float,
        conflicts: int,
    ) -> float:
        score = (
            confidence * 0.30
            + institutional_score * 0.30
            + quality * 0.20
            + stability * 0.20
        )

        score -= min(
            conflicts * 6.0,
            24.0,
        )

        return max(
            0.0,
            min(score, 100.0),
        )

    @staticmethod
    def _support_ratio(
        evidence: List[Dict[str, Any]],
        direction: str,
    ) -> float:
        directional = [
            row
            for row in evidence
            if row.get("direction")
            in {
                "bullish",
                "bearish",
            }
        ]

        if not directional:
            return 0.0

        matching = sum(
            row.get("direction") == direction
            for row in directional
        )

        return (
            matching
            / len(directional)
            * 100.0
        )

    @staticmethod
    def _stability(
        support_ratio: float,
        source_count: int,
        conflicts: int,
    ) -> float:
        diversity = min(
            source_count / 5.0,
            1.0,
        ) * 100.0

        score = (
            support_ratio * 0.65
            + diversity * 0.35
            - conflicts * 8.0
        )

        return max(
            0.0,
            min(score, 100.0),
        )

    @staticmethod
    def _apply_safety_caps(
        readiness: float,
        has_spot: bool,
        has_price_delta: bool,
        has_oi_delta: bool,
        directional_source_count: int,
    ) -> float:
        cap = 100.0

        if directional_source_count < 2:
            cap = min(
                cap,
                59.0,
            )

        if not has_spot:
            cap = min(
                cap,
                79.0,
            )

        if not has_price_delta:
            cap = min(
                cap,
                84.0,
            )

        if not has_oi_delta:
            cap = min(
                cap,
                89.0,
            )

        if directional_source_count < 3:
            cap = min(
                cap,
                89.0,
            )

        return min(
            readiness,
            cap,
        )

    @staticmethod
    def _status(
        readiness: float,
    ) -> str:
        if readiness >= 90:
            return "ACTION"

        if readiness >= 80:
            return "READY"

        if readiness >= 60:
            return "PREPARE"

        if readiness >= 30:
            return "WATCH"

        return "NO_TRADE"

    @staticmethod
    def _velocity(
        readiness: float,
        missing_count: int,
        conflicts: int,
    ) -> str:
        if conflicts >= 2:
            return "LOW"

        if (
            readiness >= 75
            and missing_count <= 2
        ):
            return "HIGH"

        if readiness >= 50:
            return "MEDIUM"

        return "LOW"

    @staticmethod
    def _eta(
        status: str,
        velocity: str,
        missing_count: int,
    ) -> str:
        if status == "ACTION":
            return "NOW"

        if status == "READY":
            return (
                "5-15 min"
                if velocity == "HIGH"
                else "10-30 min"
            )

        if status == "PREPARE":
            if velocity == "HIGH":
                return "10-25 min"

            if velocity == "MEDIUM":
                return "20-60 min"

            return "UNKNOWN"

        if status == "WATCH":
            return (
                "1-4 h"
                if missing_count <= 3
                else "UNKNOWN"
            )

        return "UNKNOWN"

    @staticmethod
    def _action(
        status: str,
        bias: str,
        has_price_delta: bool,
    ) -> str:
        if status == "ACTION":
            return (
                f"Execution window open for {bias}. "
                "Apply position and risk limits."
            )

        if status == "READY":
            return (
                f"Be ready for {bias}. "
                "Wait for the final execution trigger."
            )

        if status == "PREPARE":
            trigger = (
                "price confirmation"
                if not has_price_delta
                else "remaining confirmation"
            )

            return (
                f"Prepare for {bias}; "
                f"wait for {trigger}."
            )

        if status == "WATCH":
            return (
                "Watch only. The setup is still developing."
            )

        return (
            "No trade. Evidence is insufficient."
        )

    @staticmethod
    def _reasons(
        evidence: List[Dict[str, Any]],
    ) -> List[str]:
        ordered = sorted(
            evidence,
            key=lambda row: float(
                row.get("points") or 0.0
            ),
            reverse=True,
        )

        return [
            str(
                row.get("title")
                or row.get("description")
                or row.get("fact_type")
                or "Evidence"
            )
            for row in ordered[:5]
        ]

    @staticmethod
    def _bounded(
        value: Any,
    ) -> float:
        try:
            number = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            number = 0.0

        return max(
            0.0,
            min(number, 100.0),
        )
