from datetime import datetime, timezone

from app.execution import (
    PaperExecutionService,
)

from app.execution.paper_lifecycle import (
    PaperTradeLifecycleService,
)

from app.intelligence.market import (
    MarketSnapshot,
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

from app.performance import (
    PaperPerformanceTracker,
)


def test_ai_to_performance_flow():

    snapshot = MarketSnapshot(
        symbol="BTCUSDT",
        price=65000.0,
        volume_24h=1000000000.0,
        volatility=0.035,
        captured_at=datetime.now(
            timezone.utc
        ),
    )

    features = (
        MarketFeatureExtractor
        .extract(snapshot)
    )

    score = (
        IntelligenceScorer
        .score(features)
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
        symbol="BTCUSDT",
        side="LONG",
        price=65000.0,
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
