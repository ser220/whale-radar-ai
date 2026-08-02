from app.intelligence.early_bird.ranking_feedback_generator import (
    EarlyBirdRankingFeedbackGenerator,
)


def test_generator_creates_feedback_signal():

    generator = EarlyBirdRankingFeedbackGenerator()

    signal = generator.generate(
        pattern="REVERSAL",
        direction="SHORT",
        historical_win_rate=0.75,
    )

    assert signal.pattern == "REVERSAL"
    assert signal.direction == "SHORT"
    assert signal.confidence_adjustment > 0
    assert "historical" in signal.reason.lower()

