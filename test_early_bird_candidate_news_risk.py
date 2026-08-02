from app.intelligence.early_bird.candidate_news_risk import (
    CandidateNewsRisk,
)


def test_candidate_news_risk_contract():

    risk = CandidateNewsRisk(
        asset="HYPE",
        news_pressure_score=75.0,
        event_type="token_unlock",
        directional_bias="bearish",
        uncertainty_score=80.0,
    )

    assert risk.asset == "HYPE"
    assert risk.news_pressure_score == 75.0
    assert risk.event_type == "token_unlock"
    assert risk.directional_bias == "bearish"
    assert risk.uncertainty_score == 80.0


def test_news_risk_rejects_invalid_pressure():

    try:
        CandidateNewsRisk(
            asset="BTC",
            news_pressure_score=120.0,
            event_type="announcement",
            directional_bias="neutral",
            uncertainty_score=50.0,
        )
    except ValueError as exc:
        assert "score" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )
