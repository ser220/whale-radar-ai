from __future__ import annotations

import hashlib

from app.decision.evidence import EvidenceNode

from .models import SmartMoneyObservation


class NansenEvidenceMapper:
    """
    Converts Nansen smart money observations
    into normalized EvidenceNode objects.

    No ranking.
    No decision logic.
    No execution semantics.
    """

    def map(
        self,
        observation: SmartMoneyObservation,
    ) -> EvidenceNode:

        if not isinstance(
            observation,
            SmartMoneyObservation,
        ):
            raise TypeError(
                "observation must be SmartMoneyObservation"
            )

        direction = self._direction(
            observation
        )

        confidence = self._confidence(
            observation
        )

        strength = self._strength(
            observation
        )

        return EvidenceNode(
            id=self._id(
                observation
            ),
            fact_type="smart_money_flow",
            title=(
                "Nansen Smart Money Flow"
            ),
            direction=direction,
            confidence=confidence,
            strength=strength,
            source="nansen",
            metadata={
                "asset": observation.asset,
                "chain": observation.chain,
                "net_flow_24h_usd": (
                    observation.net_flow_24h_usd
                ),
                "net_flow_7d_usd": (
                    observation.net_flow_7d_usd
                ),
                "net_flow_30d_usd": (
                    observation.net_flow_30d_usd
                ),
                "trader_count": (
                    observation.trader_count
                ),
                "market_cap_usd": (
                    observation.market_cap_usd
                ),
                "observed_at": (
                    observation.observed_at
                ),
            },
        )

    @staticmethod
    def _direction(
        observation: SmartMoneyObservation,
    ) -> str:

        if observation.net_flow_7d_usd > 0:
            return "bullish"

        if observation.net_flow_7d_usd < 0:
            return "bearish"

        return "neutral"

    @staticmethod
    def _confidence(
        observation: SmartMoneyObservation,
    ) -> float:

        if observation.trader_count >= 100:
            return 85.0

        if observation.trader_count >= 10:
            return 70.0

        return 55.0

    @staticmethod
    def _strength(
        observation: SmartMoneyObservation,
    ) -> str:

        absolute_flow = abs(
            observation.net_flow_7d_usd
        )

        if absolute_flow >= 1_000_000:
            return "strong"

        if absolute_flow >= 100_000:
            return "moderate"

        return "weak"

    @staticmethod
    def _id(
        observation: SmartMoneyObservation,
    ) -> str:

        raw = "|".join(
            [
                observation.asset,
                observation.chain,
                str(
                    observation.observed_at
                ),
            ]
        )

        digest = hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()[:12]

        return (
            f"{observation.asset.lower()}"
            f"-nansen-smart-money-{digest}"
        )
