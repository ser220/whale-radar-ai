from datetime import datetime, timezone

from app.simulation import (
    SimulationSnapshot,
    SimulationMarketAdapter,
)

from app.intelligence.features import (
    MarketFeatureExtractor,
)

from app.intelligence.scoring import (
    IntelligenceScorer,
)

from app.intelligence.risk import (
    RiskEvaluator,
)

from app.intelligence.confidence import (
    ConfidenceAggregator,
)

from app.execution import (
    PaperExecutionService,
)

from app.execution.paper_lifecycle import (
    PaperTradeLifecycleService,
)

from app.performance import (
    PaperPerformanceTracker,
)


def test_simulation_full_trade_flow():

    simulation_snapshot = SimulationSnapshot(
        symbol="BTCUSDT",
        price=65000.0,
        volume_24h=1000000000.0,
        volatility=0.035,
        timestamp=datetime.now(
            timezone.utc
        ),
    )

    market_snapshot = (
        SimulationMarketAdapter
        .to_market_snapshot(
            simulation_snapshot
        )
    )

    features = (
        MarketFeatureExtractor
        .extract(
            market_snapshot
        )
    )

    score = (
        IntelligenceScorer
        .score(
            features
        )
    )

    risk = (
        RiskEvaluator
        .evaluate(
            features,
            score,
        )
    )

    confidence = (
        ConfidenceAggregator
        .aggregate(
            score,
            risk,
        )
    )

    assert (
        confidence.confidence
        > 0
    )

    execution = PaperExecutionService()

    trade = execution.open_trade(
        symbol=market_snapshot.symbol,
        side="LONG",
        price=market_snapshot.price,
        quantity=0.01,
    )

    lifecycle = PaperTradeLifecycleService()

    result = lifecycle.close_trade(
        trade,
        exit_price=67000.0,
    )

    tracker = PaperPerformanceTracker()

    report = tracker.calculate(
        [result]
    )

    assert (
        report.total_trades
        == 1
    )

    assert (
        report.winning_trades
        == 1
    )

    assert (
        report.total_pnl
        > 0
    )
