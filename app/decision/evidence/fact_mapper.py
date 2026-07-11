import hashlib
from typing import Iterable, List

from app.decision.evidence.node import EvidenceNode
from app.decision.facts import MarketFact


class MarketFactEvidenceMapper:
    """
    Converts normalized MarketFact objects into EvidenceNode objects.
    """

    SOURCE_WEIGHTS = {
        "arkham": 1.30,
        "wallet": 1.25,
        "spot_cvd": 1.20,
        "spot_echo": 1.15,
        "liquidations": 1.15,
        "campaign": 1.10,
        "oi": 1.10,
        "open_interest": 1.10,
        "funding": 1.00,
        "basis": 0.90,
        "price_delta": 0.85,
        "history": 0.80,
    }

    STRENGTH_WEIGHTS = {
        "weak": 0.40,
        "moderate": 0.65,
        "strong": 0.85,
        "extreme": 1.00,
    }

    def map_fact(
        self,
        fact: MarketFact,
        position: int = 0,
    ) -> EvidenceNode:
        if not isinstance(
            fact,
            MarketFact,
        ):
            raise TypeError(
                "fact must be MarketFact."
            )

        node_id = self._node_id(
            fact=fact,
            position=position,
        )

        weight = self._weight(
            fact
        )

        metadata = dict(
            fact.metadata
        )

        metadata.update({
            "description": (
                fact.description
            ),
            "value": fact.value,
            "unit": fact.unit,
            "exchange": fact.exchange,
            "timestamp": fact.timestamp,
        })

        return EvidenceNode(
            id=node_id,
            fact_type=fact.fact_type,
            title=fact.title,
            direction=fact.direction,
            confidence=fact.confidence,
            strength=fact.strength,
            source=fact.source,
            weight=weight,
            metadata=metadata,
        )

    def map_many(
        self,
        facts: Iterable[MarketFact],
    ) -> List[EvidenceNode]:
        nodes = []

        for position, fact in enumerate(
            facts
        ):
            nodes.append(
                self.map_fact(
                    fact=fact,
                    position=position,
                )
            )

        return nodes

    def _weight(
        self,
        fact: MarketFact,
    ) -> float:
        source_weight = (
            self.SOURCE_WEIGHTS.get(
                fact.source,
                0.75,
            )
        )

        strength_weight = (
            self.STRENGTH_WEIGHTS.get(
                fact.strength,
                0.65,
            )
        )

        confidence_weight = (
            fact.confidence
            / 100.0
        )

        return round(
            25.0
            * source_weight
            * strength_weight
            * confidence_weight,
            2,
        )

    @staticmethod
    def _node_id(
        fact: MarketFact,
        position: int,
    ) -> str:
        raw = "|".join([
            fact.asset,
            fact.source,
            fact.fact_type,
            fact.direction,
            str(
                fact.timestamp
            ),
            str(
                position
            ),
        ])

        digest = hashlib.sha256(
            raw.encode(
                "utf-8"
            )
        ).hexdigest()[:12]

        return (
            f"{fact.asset.lower()}-"
            f"{fact.source}-"
            f"{fact.fact_type}-"
            f"{digest}"
        )
