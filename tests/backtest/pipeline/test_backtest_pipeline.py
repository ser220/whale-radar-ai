from app.backtest.pipeline import (
    BacktestPipelineOrchestrator,
    BacktestPipelineResult,
)
from app.backtest.report import (
    BacktestFinalReport,
)
from app.backtest.review import (
    AIReviewGenerator,
    BacktestAIReview,
)
from app.backtest.summary import (
    AISummaryGenerator,
    BacktestAISummary,
)


class FalsyAISummaryGenerator(
    AISummaryGenerator
):
    def __init__(self) -> None:
        self.called = False

    def __bool__(self) -> bool:
        return False

    def generate(
        self,
        strategy_id: str,
        decision: str,
        score: float,
        risk_level: str,
        confidence: float,
    ) -> BacktestAISummary:
        self.called = True

        return BacktestAISummary(
            strategy_id=strategy_id,
            decision=decision,
            headline="Injected summary",
            explanation="Falsy summary generator was invoked",
            risk_level=risk_level,
            confidence=confidence,
        )


class FalsyAIReviewGenerator(
    AIReviewGenerator
):
    def __init__(self) -> None:
        self.called = False

    def __bool__(self) -> bool:
        return False

    def generate(
        self,
        strategy_id: str,
        decision: str,
        confidence: float,
    ) -> BacktestAIReview:
        self.called = True

        return BacktestAIReview(
            strategy_id=strategy_id,
            verdict="APPROVE",
            production_readiness="READY",
            strengths=(
                "Injected review",
            ),
            risks=(
                "Injected review risk",
            ),
            recommended_actions=(
                "Injected review action",
            ),
            confidence=confidence,
        )


def test_backtest_pipeline() -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-alpha",
        decision="PASS",
        rank=1,
        score=92.0,
        confidence=0.92,
        summary="Strong performance",
    )

    result = (
        BacktestPipelineOrchestrator()
        .run(
            report=report,
            risk_level="LOW",
        )
    )

    assert isinstance(
        result,
        BacktestPipelineResult,
    )

    assert (
        result.report.strategy_id
        == "strategy-alpha"
    )

    assert (
        result.summary.decision
        == "PASS"
    )

    assert (
        result.review.verdict
        == "APPROVE"
    )


def test_orchestrator_invokes_injected_falsy_generators() -> None:
    summary_generator = FalsyAISummaryGenerator()
    review_generator = FalsyAIReviewGenerator()
    report = BacktestFinalReport(
        strategy_id="strategy-injected",
        decision="PASS",
        rank=1,
        score=91.0,
        confidence=0.91,
        summary="Injected dependency test",
    )

    result = BacktestPipelineOrchestrator(
        summary_generator=summary_generator,
        review_generator=review_generator,
    ).run(
        report=report,
        risk_level="LOW",
    )

    assert isinstance(
        result,
        BacktestPipelineResult,
    )
    assert summary_generator.called is True
    assert review_generator.called is True
    assert result.summary.headline == (
        "Injected summary"
    )
    assert result.review.strengths == (
        "Injected review",
    )


def test_orchestrator_explicit_none_uses_default_generators() -> None:
    report = BacktestFinalReport(
        strategy_id="strategy-default",
        decision="PASS",
        rank=1,
        score=90.0,
        confidence=0.90,
        summary="Default dependency test",
    )

    result = BacktestPipelineOrchestrator(
        summary_generator=None,
        review_generator=None,
    ).run(
        report=report,
        risk_level="LOW",
    )

    assert isinstance(
        result,
        BacktestPipelineResult,
    )
    assert result.summary.headline == (
        "Strategy approved"
    )
    assert result.review.strengths == (
        "Strong backtest performance",
        "Acceptable risk profile",
    )
