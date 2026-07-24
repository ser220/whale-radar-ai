import pytest

from app.backtest.review import (
    AIReviewGenerator,
    BacktestAIReview,
)


def test_backtest_ai_review_model() -> None:
    review = BacktestAIReview(
        strategy_id="strategy-alpha",
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

    assert review.strategy_id == "strategy-alpha"
    assert review.verdict == "APPROVE"
    assert review.production_readiness == "READY"
    assert review.confidence == 0.92


def test_ai_review_generator_pass() -> None:
    review = AIReviewGenerator().generate(
        strategy_id="strategy-alpha",
        decision="PASS",
        confidence=0.92,
    )

    assert isinstance(
        review,
        BacktestAIReview,
    )
    assert review.verdict == "APPROVE"
    assert review.production_readiness == "READY"
    assert review.recommended_actions == (
        "Deploy with standard monitoring",
    )


def test_ai_review_generator_review() -> None:
    review = AIReviewGenerator().generate(
        strategy_id="strategy-beta",
        decision="REVIEW",
        confidence=0.70,
    )

    assert review.verdict == "CONDITIONAL"
    assert review.production_readiness == "LIMITED"
    assert review.confidence == 0.70


def test_ai_review_generator_reject() -> None:
    review = AIReviewGenerator().generate(
        strategy_id="strategy-gamma",
        decision="REJECT",
        confidence=0.40,
    )

    assert review.verdict == "REJECT"
    assert review.production_readiness == "NOT_READY"
    assert review.confidence == 0.40


@pytest.mark.parametrize(
    "decision",
    [
        "",
        " ",
        "UNKNOWN",
        "pass",
        "REVEIW",
        " pass ",
        "PASS ",
        " pass",
    ],
)
def test_ai_review_generator_rejects_invalid_decision_without_normalizing(
    decision: str,
) -> None:
    with pytest.raises(ValueError) as raised:
        AIReviewGenerator().generate(
            strategy_id="strategy-invalid",
            decision=decision,
            confidence=0.50,
        )

    assert str(raised.value) == (
        "invalid decision"
    )


def test_backtest_ai_review_rejects_invalid_confidence() -> None:
    with pytest.raises(
        ValueError,
        match="confidence must be between 0 and 1",
    ):
        BacktestAIReview(
            strategy_id="strategy-alpha",
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
            confidence=1.10,
        )
