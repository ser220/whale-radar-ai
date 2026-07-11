from typing import Dict, List, Optional

from app.decision.evidence.edge import EvidenceEdge
from app.decision.evidence.node import EvidenceNode


class EvidenceGraph:
    """
    Container for normalized evidence nodes and relationships.
    """

    def __init__(self) -> None:
        self.nodes: Dict[str, EvidenceNode] = {}
        self.edges: List[EvidenceEdge] = []

    def add_node(
        self,
        node: EvidenceNode,
    ) -> None:
        self.nodes[node.id] = node

    def add_edge(
        self,
        edge: EvidenceEdge,
    ) -> None:
        if edge.source not in self.nodes:
            raise KeyError(
                f"Unknown source node: {edge.source}"
            )

        if edge.target not in self.nodes:
            raise KeyError(
                f"Unknown target node: {edge.target}"
            )

        self.edges.append(edge)

    def get(
        self,
        node_id: str,
    ) -> Optional[EvidenceNode]:
        return self.nodes.get(
            node_id
        )

    def outgoing(
        self,
        node_id: str,
    ) -> List[EvidenceEdge]:
        return [
            edge
            for edge in self.edges
            if edge.source == node_id
        ]

    def incoming(
        self,
        node_id: str,
    ) -> List[EvidenceEdge]:
        return [
            edge
            for edge in self.edges
            if edge.target == node_id
        ]

    def summary(
        self,
    ) -> dict:
        return {
            "nodes": len(
                self.nodes
            ),
            "edges": len(
                self.edges
            ),
        }
