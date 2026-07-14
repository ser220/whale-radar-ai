"""Isolated collection and evaluation of already-produced expert opinions."""

from datetime import datetime
from typing import Dict, Mapping, Optional, Tuple

from app.intelligence.contracts import ExpertOpinion, MarketState
from app.intelligence.market_state import MarketStateEngine


class ShadowIntelligenceEngine:
    """Collect independent opinions and delegate synthesis to MarketStateEngine.

    This in-memory layer performs no provider calls or persistence. Opinions are
    retained in deterministic registration order and remain owned by their
    producing experts.
    """

    def __init__(
        self,
        market_state_engine: Optional[MarketStateEngine] = None,
    ) -> None:
        if market_state_engine is not None and not isinstance(
            market_state_engine, MarketStateEngine
        ):
            raise TypeError("market_state_engine must be a MarketStateEngine")
        self._market_state_engine = market_state_engine or MarketStateEngine()
        self._opinions: Dict[str, ExpertOpinion] = {}

    @property
    def market_state_engine(self) -> MarketStateEngine:
        """Return the synthesis authority used by this shadow evaluator."""
        return self._market_state_engine

    def add_opinion(self, opinion: ExpertOpinion) -> None:
        """Register one immutable opinion, rejecting duplicate expert names."""
        if not isinstance(opinion, ExpertOpinion):
            raise TypeError("opinion must be an ExpertOpinion")
        if opinion.expert_name in self._opinions:
            raise ValueError(
                "duplicate expert opinion: {0}".format(opinion.expert_name)
            )
        self._opinions[opinion.expert_name] = opinion

    def get_opinions(self) -> Tuple[ExpertOpinion, ...]:
        """Return a read-only snapshot in deterministic registration order."""
        return tuple(self._opinions.values())

    def evaluate(
        self,
        *,
        weights: Optional[Mapping[str, float]] = None,
        timestamp: Optional[datetime] = None,
    ) -> MarketState:
        """Synthesize the current snapshot without changing stored opinions."""
        return self._market_state_engine.synthesize(
            self.get_opinions(),
            weights=weights,
            timestamp=timestamp,
        )
