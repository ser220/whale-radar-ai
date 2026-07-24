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


class ContradictoryReviewLike:
    strategy_id = "strategy-contract"
    verdict = "REJECT"
    production_readiness = "NOT_READY"
    confidence = 0.92


def _build_report(
    decision: str = "PASS",
) -> BacktestFinalReport:
    return BacktestFinalReport(
        strategy_id="strategy-contract",
        decision=decision,
        rank=1,
        score=92.0,
        confidence=0.92,
        summary="Strong performance",
    )


def _build_summary(
    decision: str = "PASS",
) -> BacktestAISummary:
    return BacktestAISummary(
        strategy_id="strategy-contract",
        decision=decision,
        headline="Strategy approved",
        explanation="Strong performance",
        risk_level="LOW",
        confidence=0.92,
    )


def _build_review(
    verdict: str = "APPROVE",
    production_readiness: str = "READY",
) -> BacktestAIReview:
    return BacktestAIReview(
        strategy_id="strategy-contract",
        verdict=verdict,
        production_readiness=(
            production_readiness
        ),
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


@pytest.mark.parametrize(
    (
        "decision",
        "verdict",
        "production_readiness",
    ),
    [
        (
            "PASS",
            "APPROVE",
            "READY",
        ),
        (
            "REVIEW",
            "CONDITIONAL",
            "LIMITED",
        ),
        (
            "REJECT",
            "REJECT",
            "NOT_READY",
        ),
    ],
)
def test_pipeline_result_accepts_consistent_decision_review_states(
    decision: str,
    verdict: str,
    production_readiness: str,
) -> None:
    result = BacktestPipelineResult(
        report=_build_report(
            decision=decision,
        ),
        summary=_build_summary(
            decision=decision,
        ),
        review=_build_review(
            verdict=verdict,
            production_readiness=(
                production_readiness
            ),
        ),
    )

    assert result.summary.decision == decision
    assert result.review.verdict == verdict
    assert (
        result.review.production_readiness
        == production_readiness
    )


@pytest.mark.parametrize(
    (
        "decision",
        "verdict",
        "production_readiness",
    ),
    [
        (
            "PASS",
            "REJECT",
            "NOT_READY",
        ),
        (
            "REVIEW",
            "APPROVE",
            "READY",
        ),
        (
            "REJECT",
            "CONDITIONAL",
            "LIMITED",
        ),
        (
            "PASS",
            "REJECT",
            "READY",
        ),
        (
            "PASS",
            "APPROVE",
            "NOT_READY",
        ),
    ],
)
def test_pipeline_result_rejects_inconsistent_decision_review_states(
    decision: str,
    verdict: str,
    production_readiness: str,
) -> None:
    with pytest.raises(ValueError) as raised:
        BacktestPipelineResult(
            report=_build_report(
                decision=decision,
            ),
            summary=_build_summary(
                decision=decision,
            ),
            review=_build_review(
                verdict=verdict,
                production_readiness=(
                    production_readiness
                ),
            ),
        )

    assert str(raised.value) == (
        "summary decision and review state must match"
    )


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


def test_nested_type_validation_precedes_decision_review_consistency(
) -> None:
    with pytest.raises(TypeError) as raised:
        BacktestPipelineResult(
            report=_build_report(),
            summary=_build_summary(),
            review=ContradictoryReviewLike(),
        )

    assert str(raised.value) == (
        "review must be BacktestAIReview"
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
