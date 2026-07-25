import math
from dataclasses import FrozenInstanceError, fields

import pytest

from app.risk import RiskComponent, RiskFactor, RiskLevel


def build_component(**overrides) -> RiskComponent:
    values = {
        "factor": RiskFactor.FUNDING,
        "score": 42.5,
        "level": RiskLevel.MEDIUM,
        "reason_code": "FUNDING_RATE_ELEVATED",
    }
    values.update(overrides)
    return RiskComponent(**values)


def test_fields_are_exact() -> None:
    assert [field.name for field in fields(RiskComponent)] == [
        "factor",
        "score",
        "level",
        "reason_code",
    ]


def test_component_is_frozen_hashable_and_deterministic() -> None:
    first = build_component()
    second = build_component()

    assert first == second
    assert hash(first) == hash(second)
    assert {first, second} == {first}

    with pytest.raises(FrozenInstanceError):
        first.score = 0.0


def test_integer_score_normalizes_to_float() -> None:
    component = build_component(score=25)

    assert component.score == 25.0
    assert isinstance(component.score, float)


@pytest.mark.parametrize("score", [True, False])
def test_bool_score_is_rejected(score) -> None:
    with pytest.raises(TypeError, match="score must be a real number"):
        build_component(score=score)


@pytest.mark.parametrize(
    "score",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_non_finite_score_is_rejected(score) -> None:
    with pytest.raises(ValueError, match="score must be finite"):
        build_component(score=score)


@pytest.mark.parametrize("score", [-0.1, 100.1])
def test_score_outside_range_is_rejected(score) -> None:
    with pytest.raises(ValueError, match="score must be within 0..100"):
        build_component(score=score)


def test_invalid_factor_is_rejected() -> None:
    with pytest.raises(TypeError, match="factor must be a RiskFactor"):
        build_component(factor="FUNDING")


def test_invalid_level_is_rejected() -> None:
    with pytest.raises(TypeError, match="level must be a RiskLevel"):
        build_component(level="HIGH")


def test_reason_code_requires_string() -> None:
    with pytest.raises(TypeError, match="reason_code must be a string"):
        build_component(reason_code=None)


def test_valid_component_preserves_values() -> None:
    component = build_component()

    assert component.factor is RiskFactor.FUNDING
    assert math.isclose(component.score, 42.5)
    assert component.level is RiskLevel.MEDIUM
    assert component.reason_code == "FUNDING_RATE_ELEVATED"
