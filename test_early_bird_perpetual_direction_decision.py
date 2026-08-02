from app.intelligence.early_bird.perpetual_direction_decision import (
    PerpetualDirectionDecision,
)


def test_direction_decision_contract():

    decision = PerpetualDirectionDecision(
        asset="HYPE",
        direction="SHORT",
        confidence=84.0,
        market_regime="bullish_exhaustion",
        reason=(
            "pump exhaustion with bearish reversal"
        ),
        risk_flags=(
            "high_funding",
            "negative_news",
        ),
    )

    assert decision.asset == "HYPE"
    assert decision.direction == "SHORT"
    assert decision.confidence == 84.0
    assert (
        decision.market_regime
        ==
        "bullish_exhaustion"
    )



def test_invalid_confidence_rejected():

    try:
        PerpetualDirectionDecision(
            asset="BTC",
            direction="LONG",
            confidence=120.0,
            market_regime="neutral",
            reason="invalid",
            risk_flags=(),
        )

    except ValueError as exc:
        assert "confidence" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
