from app.backtest.summary import (
    BacktestAISummary,
    AISummaryGenerator,
)


def test_backtest_ai_summary_model():

    summary = BacktestAISummary(
        strategy_id="strategy-alpha",
        decision="PASS",
        headline="Strategy approved",
        explanation="Strong performance",
        risk_level="LOW",
        confidence=0.92,
    )

    assert (
        summary.strategy_id
        == "strategy-alpha"
    )

    assert (
        summary.decision
        == "PASS"
    )

    assert (
        summary.confidence
        == 0.92
    )


def test_ai_summary_generator():

    summary = (
        AISummaryGenerator()
        .generate(
            strategy_id="strategy-alpha",
            decision="PASS",
            score=92.0,
            risk_level="LOW",
            confidence=0.92,
        )
    )

    assert isinstance(
        summary,
        BacktestAISummary,
    )

    assert (
        summary.headline
        == "Strategy approved"
    )

    assert (
        summary.risk_level
        == "LOW"
    )
