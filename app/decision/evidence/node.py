from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(slots=True)
class EvidenceNode:
    """
    One normalized piece of evidence.
    """

    id: str
    fact_type: str
    title: str
    direction: str
    confidence: float
    strength: str
    source: str

    weight: float = 0.0

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def is_bullish(self) -> bool:
        return self.direction == "bullish"

    def is_bearish(self) -> bool:
        return self.direction == "bearish"

    def is_neutral(self) -> bool:
        return self.direction == "neutral"
