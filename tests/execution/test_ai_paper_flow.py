from datetime import datetime, timezone

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

from app.execution import (
    PaperExecutionService,
)


def test_ai_to_paper_trade_flow():
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
        symbol=snapshot.symbol,
        side="LONG",
        price=snapshot.price,
        quantity=0.01,
    )

    assert (
        trade.symbol
        == "BTCUSDT"
    )

    assert (
        trade.status
        == "OPEN"
    )
