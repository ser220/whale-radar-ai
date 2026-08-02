"""Early Bird runtime orchestration boundary."""

from dataclasses import dataclass

from app.intelligence.early_bird.market_sweep_result import (
    EarlyBirdMarketSweepResult,
)

from app.intelligence.early_bird.candidate_news_risk import (
    CandidateNewsRisk,
)

from app.intelligence.early_bird.directional_analyzer import (
    DirectionalAnalyzer,
)

from app.intelligence.early_bird.news_impact_aggregator import (
    NewsImpactAggregator,
)

from app.intelligence.early_bird.perpetual_direction_resolver import (
    PerpetualDirectionResolver,
)
from app.intelligence.early_bird.directional_analyzer import (
    DirectionalAnalyzer,
)
from app.intelligence.early_bird.rank_cascade_engine import (
    RankCascadeEngine,
)
from app.intelligence.early_bird.candidate_dual_rank import (
    CandidateDualRank,
)

from app.intelligence.early_bird.candidate_selection_result import (
    CandidateSelectionResult,
)

from app.intelligence.early_bird.candidate_ranking_record import (
    CandidateRankingRecord,
)

from app.intelligence.early_bird.leaderboard_ranking_aggregator import (
    LeaderboardRankingAggregator,
)

from app.intelligence.early_bird.perpetual_opportunity_selector import (
    PerpetualOpportunitySelector,
)


@dataclass(frozen=True)
class EarlyBirdRuntimeResult:
    """Result of one Early Bird runtime cycle."""

    market_sweep: EarlyBirdMarketSweepResult | None = None
    cascade_rank: CandidateDualRank | None = None
    selection_result: CandidateSelectionResult | None = None
    direction_decision: object | None = None
    leaderboard: object | None = None
    opportunity: object | None = None


class EarlyBirdRuntime:
    """Coordinates one Early Bird processing cycle."""

    def __init__(self) -> None:
        self._directional_analyzer = DirectionalAnalyzer()
        self._rank_cascade_engine = RankCascadeEngine()
        self._news_aggregator = NewsImpactAggregator()
        self._direction_resolver = PerpetualDirectionResolver()
        self._leaderboard_aggregator = LeaderboardRankingAggregator()
        self._opportunity_selector = PerpetualOpportunitySelector()

    def process(
        self,
        market_sweep: EarlyBirdMarketSweepResult,
    ) -> EarlyBirdRuntimeResult:
        if not isinstance(
            market_sweep,
            EarlyBirdMarketSweepResult,
        ):
            raise TypeError(
                "market_sweep must be EarlyBirdMarketSweepResult"
            )

        return EarlyBirdRuntimeResult(
            market_sweep=market_sweep,
        )


    def process_selection(
        self,
        selection_result: CandidateSelectionResult,
    ) -> EarlyBirdRuntimeResult:

        if not isinstance(
            selection_result,
            CandidateSelectionResult,
        ):
            raise TypeError(
                "selection_result must be CandidateSelectionResult"
            )

        return EarlyBirdRuntimeResult(
            selection_result=selection_result,
        )


    def process_perpetual_cycle(
        self,
        *,
        asset: str,
        signals: dict,
        news_risk: dict,
    ) -> EarlyBirdRuntimeResult:

        directional = self._directional_analyzer.analyze(
            signals,
        )

        directional = directional.__class__(
            asset=asset,
            long_score=directional.long_score,
            short_score=directional.short_score,
            long_rank=directional.long_rank,
            short_rank=directional.short_rank,
            market_regime=directional.market_regime,
            confidence=directional.confidence,
        )

        news = CandidateNewsRisk(
            asset=asset,
            **news_risk,
        )

        adjusted = self._news_aggregator.apply(
            directional,
            news,
        )

        decision = self._direction_resolver.resolve(
            adjusted,
            market_regime=directional.market_regime,
        )

        return EarlyBirdRuntimeResult(
            direction_decision=decision,
        )


    def process_full_cycle(
        self,
        *,
        asset: str,
        signals: dict,
        selection_result: CandidateSelectionResult | None = None,
    ) -> EarlyBirdRuntimeResult:

        directional = self._directional_analyzer.analyze(
            signals,
        )

        cascade_rank = self._rank_cascade_engine.evaluate(
            asset=asset,
            long_score=directional.long_score,
            short_score=directional.short_score,
        )

        return EarlyBirdRuntimeResult(
            cascade_rank=cascade_rank,
            selection_result=selection_result,
        )

    def process_signals(
        self,
        *,
        asset: str,
        signals: dict,
    ) -> EarlyBirdRuntimeResult:

        directional = self._directional_analyzer.analyze(
            signals,
        )

        cascade_rank = self._rank_cascade_engine.evaluate(
            asset=asset,
            long_score=directional.long_score,
            short_score=directional.short_score,
        )

        return EarlyBirdRuntimeResult(
            cascade_rank=cascade_rank,
        )


    def process_cascade_pipeline(
        self,
        *,
        asset: str,
        long_score: float,
        short_score: float,
    ) -> EarlyBirdRuntimeResult:

        cascade = self._rank_cascade_engine.evaluate(
            asset=asset,
            long_score=long_score,
            short_score=short_score,
        )

        records = []

        if cascade.long_score > 0:
            records.append(
                CandidateRankingRecord(
                    asset=asset,
                    direction="LONG",
                    rank=cascade.long_rank,
                    score=cascade.long_score,
                    confidence=cascade.long_score,
                    risk_score=20,
                    priority=cascade.long_score,
                )
            )

        if cascade.short_score >= 60:
            records.append(
                CandidateRankingRecord(
                    asset=asset,
                    direction="SHORT",
                    rank=cascade.short_rank,
                    score=cascade.short_score,
                    confidence=cascade.short_score,
                    risk_score=20,
                    priority=cascade.short_score,
                )
            )

        leaderboard = self._leaderboard_aggregator.aggregate(
            records
        )

        opportunity = self._opportunity_selector.select(
            leaderboard
        )

        return EarlyBirdRuntimeResult(
            cascade_rank=cascade,
            leaderboard=leaderboard,
            opportunity=opportunity,
        )


__all__ = [
    "EarlyBirdRuntime",
    "EarlyBirdRuntimeResult",
]
