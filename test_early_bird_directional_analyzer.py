from app.intelligence.early_bird.directional_analyzer import (
    DirectionalAnalyzer,
)


def test_analyzer_detects_long_continuation():

    result = DirectionalAnalyzer().analyze(
        {
            "momentum": 85,
            "volume": 80,
            "oi_health": 75,
            "exhaustion": 10,
            "bearish_structure": 5,
        }
    )

    assert result.long_score > 70
    assert result.short_score < 40
    assert (
        result.market_regime
        ==
        "bullish_continuation"
    )


def test_analyzer_detects_reversal_risk():

    result = DirectionalAnalyzer().analyze(
        {
            "momentum": 40,
            "volume": 30,
            "oi_health": 80,
            "exhaustion": 90,
            "bearish_structure": 85,
        }
    )

    assert result.short_score > 70
    assert (
        result.market_regime
        ==
        "bullish_exhaustion"
    )
