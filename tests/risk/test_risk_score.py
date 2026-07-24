from dataclasses import FrozenInstanceError

import pytest

from app.risk import RiskLevel, RiskScore


def build_risk_score() -> RiskScore:
    return RiskScore(
        total_score=62.5,
        liquidity_score=55.0,
        funding_score=60.0,
        whale_score=75.0,
        flow_score=65.0,
        volatility_score=57.5,
    )


def test_valid_risk_score_construction() -> None:
    score = build_risk_score()

    assert score.total_score == 62.5
    assert score.liquidity_score == 55.0
    assert score.funding_score == 60.0
    assert score.whale_score == 75.0
    assert score.flow_score == 65.0
    assert score.volatility_score == 57.5


def test_risk_score_value_equality() -> None:
    assert build_risk_score() == build_risk_score()


def test_risk_score_is_immutable() -> None:
    score = build_risk_score()

    with pytest.raises(FrozenInstanceError):
        score.total_score = 10.0


def test_risk_score_is_hashable() -> None:
    first = build_risk_score()
    second = build_risk_score()

    assert hash(first) == hash(second)
    assert {first, second} == {first}


def test_risk_level_mapping() -> None:
    expected = {
        "LOW": RiskLevel.LOW,
        "MEDIUM": RiskLevel.MEDIUM,
        "HIGH": RiskLevel.HIGH,
        "EXTREME": RiskLevel.EXTREME,
    }

    assert {
        level.value: level
        for level in RiskLevel
    } == expected

    for value, level in expected.items():
        assert RiskLevel(value) is level
