from app.intelligence.early_bird.perpetual_position_builder import (
    PerpetualPositionBuilder,
)

from app.intelligence.early_bird.perpetual_opportunity import (
    PerpetualOpportunity,
)


def test_position_builder_creates_preparation():

    opportunity = PerpetualOpportunity(
        asset="HYPE",
        direction="LONG",
        setup_type="CONTINUATION",
        rank="L4",
        score=90,
        priority=90,
        confidence=90,
        reason="strong continuation",
    )

    result = PerpetualPositionBuilder().build(
        opportunity
    )

    assert result.asset == "HYPE"
    assert result.direction == "LONG"
    assert result.entry_mode == "LIMIT"
    assert result.dca_allowed is True
