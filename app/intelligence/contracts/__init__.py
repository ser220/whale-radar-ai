"""Stable domain contracts shared by future intelligence components.

This package is intentionally independent from transport, persistence, data
sources, and the current production pipeline.
"""

from app.intelligence.contracts.enums import Direction, LifecycleState, TrendState
from app.intelligence.contracts.models import DecisionState, ExpertOpinion, MarketState
from app.intelligence.contracts.registry import ExpertRegistry

__all__ = [
    "DecisionState",
    "Direction",
    "ExpertOpinion",
    "ExpertRegistry",
    "LifecycleState",
    "MarketState",
    "TrendState",
]
