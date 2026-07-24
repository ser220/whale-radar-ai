import pytest

from app.backtest.pipeline import (
    BacktestPipelineResult,
)
from app.backtest.report import (
    BacktestFinalReport,
)
from app.backtest.review import (
    BacktestAIReview,
)
from app.backtest.summary import (
    BacktestAISummary,
)


class SpecializedFinalReport(
    BacktestFinalReport
):
    pass


class SpecializedAISummary(
    BacktestAISummary
):
    pass


class SpecializedAIReview(
    BacktestAIReview
):
    pass


def _build_report() -> BacktestFinalReport:
    return BacktestFinalReport(
        strategy_id="strategy-contract",
        decision="PASS",
        rank=1,
        score=92.0,
        confidence=0.92,
        summary="Strong performance",
    )


def _build_summary() -> BacktestAISummary:
    return BacktestAISummary(
        strategy_id="strategy-contract",
        decision="PASS",
        headline="Strategy approved",
        explanation="Strong performance",
        risk_level="LOW",
        confidence=0.92,
    )


def _build_review() -> BacktestAIReview:
    return BacktestAIReview(
        strategy_id="strategy-contract",
        verdict="APPROVE",
        production_readiness="READY",
        strengths=(
            "Strong backtest performance",
        ),
        risks=(
            "Future market conditions may differ",
        ),
        recommended_actions=(
            "Deploy with standard monitoring",
        ),
        confidence=0.92,
    )


def test_pipeline_result_accepts_valid_nested_contracts() -> None:
    report = _build_report()
    summary = _build_summary()
    review = _build_review()

    result = BacktestPipelineResult(
        report=report,
        summary=summary,
        review=review,
    )

    assert result.report is report
    assert result.summary is summary
    assert result.review is review


def test_pipeline_result_rejects_invalid_report_before_attribute_access(
) -> None:
    with pytest.raises(
        TypeError,
        match="report must be BacktestFinalReport",
    ):
        BacktestPipelineResult(
            report=object(),
            summary=_build_summary(),
            review=_build_review(),
        )


def test_pipeline_result_rejects_invalid_summary_before_attribute_access(
) -> None:
    with pytest.raises(
        TypeError,
        match="summary must be BacktestAISummary",
    ):
        BacktestPipelineResult(
            report=_build_report(),
            summary=object(),
            review=_build_review(),
        )


def test_pipeline_result_rejects_invalid_review_before_attribute_access(
) -> None:
    with pytest.raises(
        TypeError,
        match="review must be BacktestAIReview",
    ):
        BacktestPipelineResult(
            report=_build_report(),
            summary=_build_summary(),
            review=object(),
        )


def test_pipeline_result_accepts_nested_contract_subclasses() -> None:
    report = SpecializedFinalReport(
        strategy_id="strategy-contract",
        decision="PASS",
        rank=1,
        score=92.0,
        confidence=0.92,
        summary="Strong performance",
    )
    summary = SpecializedAISummary(
        strategy_id="strategy-contract",
        decision="PASS",
        headline="Strategy approved",
        explanation="Strong performance",
        risk_level="LOW",
        confidence=0.92,
    )
    review = SpecializedAIReview(
        strategy_id="strategy-contract",
        verdict="APPROVE",
        production_readiness="READY",
        strengths=(
            "Strong backtest performance",
        ),
        risks=(
            "Future market conditions may differ",
        ),
        recommended_actions=(
            "Deploy with standard monitoring",
        ),
        confidence=0.92,
    )

    result = BacktestPipelineResult(
        report=report,
        summary=summary,
        review=review,
    )

    assert result.report is report
    assert result.summary is summary
    assert result.review is review
