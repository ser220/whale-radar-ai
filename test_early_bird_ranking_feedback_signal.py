from app.intelligence.early_bird.ranking_feedback_signal import (
    RankingFeedbackSignal,
)


def test_feedback_signal_contract():

    signal = RankingFeedbackSignal(
        pattern="REVERSAL",
        direction="SHORT",
        confidence_adjustment=10.0,
        reason="high historical win rate",
    )

    assert signal.pattern == "REVERSAL"
    assert signal.direction == "SHORT"
    assert signal.confidence_adjustment == 10.0



def test_invalid_adjustment():

    try:

        RankingFeedbackSignal(
            pattern="REVERSAL",
            direction="SHORT",
            confidence_adjustment=150.0,
            reason="invalid",
        )

    except ValueError as exc:
        assert "adjustment" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
