from typing import Iterable

from app.decision.evidence.edge import EvidenceEdge
from app.decision.evidence.graph import EvidenceGraph
from app.decision.evidence.node import EvidenceNode


class EvidenceGraphBuilder:
    """
    Builds an EvidenceGraph from normalized EvidenceNode objects.

    Current rules:

    bearish + bearish -> supports

    bullish + bullish -> supports

    bearish + bullish -> contradicts

    bullish + bearish -> contradicts

    neutral -> related
    """

    def build(
        self,
        nodes: Iterable[EvidenceNode],
    ) -> EvidenceGraph:

        graph = EvidenceGraph()

        ordered = list(nodes)

        for node in ordered:
            graph.add_node(node)

        for left in range(len(ordered)):
            for right in range(left + 1, len(ordered)):

                node_a = ordered[left]
                node_b = ordered[right]

                relation = self._relation(
                    node_a,
                    node_b,
                )

                graph.add_edge(
                    EvidenceEdge(
                        source=node_a.id,
                        target=node_b.id,
                        relation=relation,
                        strength=self._strength(
                            node_a,
                            node_b,
                        ),
                    )
                )

        return graph

    def _relation(
        self,
        a: EvidenceNode,
        b: EvidenceNode,
    ) -> str:

        if (
            a.direction == "neutral"
            or b.direction == "neutral"
        ):
            return "related"

        if a.direction == b.direction:
            return "supports"

        return "contradicts"

    def _strength(
        self,
        a: EvidenceNode,
        b: EvidenceNode,
    ) -> float:

        confidence = (
            a.confidence +
            b.confidence
        ) / 2.0

        weight = (
            a.weight +
            b.weight
        ) / 2.0

        score = (
            confidence / 100.0
        ) * (
            min(weight, 25.0) / 25.0
        )

        return round(
            score,
            2,
        )
