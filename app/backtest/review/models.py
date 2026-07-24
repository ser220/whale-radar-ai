from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class BacktestAIReview:
    """
    Final AI-style review of a backtested strategy.
    """

    strategy_id: str
    verdict: str
    production_readiness: str
    strengths: Tuple[str, ...]
    risks: Tuple[str, ...]
    recommended_actions: Tuple[str, ...]
    confidence: float

    def __post_init__(self) -> None:
        if not self.strategy_id:
            raise ValueError(
                "strategy_id cannot be empty"
            )

        if self.verdict not in {
            "APPROVE",
            "CONDITIONAL",
            "REJECT",
        }:
            raise ValueError(
                "invalid verdict"
            )

        if self.production_readiness not in {
            "READY",
            "LIMITED",
            "NOT_READY",
        }:
            raise ValueError(
                "invalid production readiness"
            )

        object.__setattr__(
            self,
            "strengths",
            tuple(self.strengths),
        )
        if not self.strengths:
            raise ValueError(
                "strengths cannot be empty"
            )

        object.__setattr__(
            self,
            "risks",
            tuple(self.risks),
        )
        if not self.risks:
            raise ValueError(
                "risks cannot be empty"
            )

        object.__setattr__(
            self,
            "recommended_actions",
            tuple(self.recommended_actions),
        )
        if not self.recommended_actions:
            raise ValueError(
                "recommended_actions cannot be empty"
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1"
            )
