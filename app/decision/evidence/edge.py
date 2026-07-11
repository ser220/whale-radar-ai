from dataclasses import dataclass


@dataclass(slots=True)
class EvidenceEdge:
    """
    Relationship between two evidence nodes.
    """

    source: str
    target: str
    relation: str
    strength: float = 1.0

    def supports(self) -> bool:
        return self.relation == "supports"

    def contradicts(self) -> bool:
        return self.relation == "contradicts"

    def related(self) -> bool:
        return self.relation == "related"
