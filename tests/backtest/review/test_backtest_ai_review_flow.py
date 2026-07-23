from app.backtest.review import (
    AIReviewGenerator,
)
from app.backtest.summary import (
    AISummaryGenerator,
)


def test_backtest_ai_review_flow() -> None:
    summary = AISummaryGenerator().generate(
        strategy_id="strategy-alpha",
        decision="PASS",
        score=92.0,
        risk_level="LOW",
        confidence=0.92,
    )

    review = AIReviewGenerator().generate(
        strategy_id=summary.strategy_id,
        decision=summary.decision,
        confidence=summary.confidence,
    )

    assert review.strategy_id == summary.strategy_id
    assert review.verdict == "APPROVE"
    assert review.production_readiness == "READY"
    assert review.confidence == summary.confidence
