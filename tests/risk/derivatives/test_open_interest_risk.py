import ast
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import get_type_hints

import pytest

import app.risk.derivatives
from app.risk import RiskComponent, RiskFactor, RiskLevel, RiskScore
from app.risk.derivatives import (
    FundingRiskEvaluator,
    FundingRiskInput,
    FundingRiskPolicy,
    OpenInterestRiskEvaluator,
    OpenInterestRiskInput,
    OpenInterestRiskPolicy,
)


OBSERVED_AT = datetime(
    2026,
    7,
    25,
    12,
    0,
    tzinfo=timezone.utc,
)


def build_input(**overrides) -> OpenInterestRiskInput:
    values = {
        "source": "normalized-open-interest",
        "symbol": "BTCUSDT",
        "open_interest": 110.0,
        "previous_open_interest": 100.0,
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return OpenInterestRiskInput(**values)


def build_policy(**overrides) -> OpenInterestRiskPolicy:
    values = {
        "extreme_change_percent": 40.0,
        "medium_score_threshold": 25.0,
        "high_score_threshold": 50.0,
        "extreme_score_threshold": 75.0,
    }
    values.update(overrides)
    return OpenInterestRiskPolicy(**values)


def evaluate(
    value: OpenInterestRiskInput,
    policy: OpenInterestRiskPolicy,
) -> RiskComponent:
    return OpenInterestRiskEvaluator().evaluate(value, policy)


def test_input_fields_are_exact() -> None:
    assert [field.name for field in fields(OpenInterestRiskInput)] == [
        "source",
        "symbol",
        "open_interest",
        "previous_open_interest",
        "observed_at",
    ]


def test_policy_fields_are_exact() -> None:
    assert [field.name for field in fields(OpenInterestRiskPolicy)] == [
        "extreme_change_percent",
        "medium_score_threshold",
        "high_score_threshold",
        "extreme_score_threshold",
    ]


def test_input_is_frozen_hashable_and_deterministic() -> None:
    first = build_input()
    second = build_input()

    assert first == second
    assert first is not second
    assert hash(first) == hash(second)
    assert {first, second} == {first}
    with pytest.raises(FrozenInstanceError):
        first.open_interest = 120.0


def test_policy_is_frozen_hashable_and_deterministic() -> None:
    first = build_policy()
    second = build_policy()

    assert first == second
    assert first is not second
    assert hash(first) == hash(second)
    assert {first, second} == {first}
    with pytest.raises(FrozenInstanceError):
        first.extreme_change_percent = 50.0


def test_source_is_trimmed() -> None:
    assert build_input(source="  normalized-oi  ").source == "normalized-oi"


def test_symbol_is_trimmed() -> None:
    assert build_input(symbol="  BTCUSDT  ").symbol == "BTCUSDT"


@pytest.mark.parametrize("source", ["", " ", "\t\n"])
def test_empty_or_whitespace_source_is_rejected(source) -> None:
    with pytest.raises(ValueError, match="source must not be empty"):
        build_input(source=source)


@pytest.mark.parametrize("symbol", ["", " ", "\t\n"])
def test_empty_or_whitespace_symbol_is_rejected(symbol) -> None:
    with pytest.raises(ValueError, match="symbol must not be empty"):
        build_input(symbol=symbol)


@pytest.mark.parametrize(
    ("field_name", "invalid"),
    [
        ("source", None),
        ("source", 1),
        ("symbol", None),
        ("symbol", 1),
    ],
)
def test_wrong_text_types_are_rejected(field_name, invalid) -> None:
    with pytest.raises(TypeError, match=f"{field_name} must be a string"):
        build_input(**{field_name: invalid})


@pytest.mark.parametrize(
    ("target", "field_name"),
    [
        ("input", "open_interest"),
        ("input", "previous_open_interest"),
        ("policy", "extreme_change_percent"),
        ("policy", "medium_score_threshold"),
        ("policy", "high_score_threshold"),
        ("policy", "extreme_score_threshold"),
    ],
)
def test_bool_is_rejected_for_every_numeric_field(target, field_name) -> None:
    with pytest.raises(TypeError, match=f"{field_name} must be a real number"):
        if target == "input":
            build_input(**{field_name: True})
        else:
            build_policy(**{field_name: True})


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize(
    ("target", "field_name"),
    [
        ("input", "open_interest"),
        ("input", "previous_open_interest"),
        ("policy", "extreme_change_percent"),
        ("policy", "medium_score_threshold"),
        ("policy", "high_score_threshold"),
        ("policy", "extreme_score_threshold"),
    ],
)
def test_non_finite_values_are_rejected(target, field_name, invalid) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must be finite"):
        if target == "input":
            build_input(**{field_name: invalid})
        else:
            build_policy(**{field_name: invalid})


def test_open_interest_accepts_zero_and_normalizes_integer_to_float() -> None:
    value = build_input(open_interest=0)

    assert value.open_interest == 0.0
    assert isinstance(value.open_interest, float)


def test_integer_previous_open_interest_normalizes_to_float() -> None:
    value = build_input(previous_open_interest=100)

    assert value.previous_open_interest == 100.0
    assert isinstance(value.previous_open_interest, float)


def test_integer_policy_values_normalize_to_float() -> None:
    policy = OpenInterestRiskPolicy(
        extreme_change_percent=40,
        medium_score_threshold=25,
        high_score_threshold=50,
        extreme_score_threshold=75,
    )

    assert policy == build_policy()
    assert all(
        isinstance(getattr(policy, field.name), float)
        for field in fields(OpenInterestRiskPolicy)
    )


def test_negative_open_interest_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="open_interest must be greater than or equal to 0",
    ):
        build_input(open_interest=-1.0)


@pytest.mark.parametrize("previous_open_interest", [0.0, -1.0])
def test_non_positive_previous_open_interest_is_rejected(
    previous_open_interest,
) -> None:
    with pytest.raises(
        ValueError,
        match="previous_open_interest must be greater than 0",
    ):
        build_input(previous_open_interest=previous_open_interest)


@pytest.mark.parametrize("observed_at", [None, "2026-07-25T12:00:00Z", 1])
def test_non_datetime_observed_at_is_rejected(observed_at) -> None:
    with pytest.raises(TypeError, match="observed_at must be a datetime"):
        build_input(observed_at=observed_at)


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        build_input(observed_at=datetime(2026, 7, 25, 12, 0))


def test_aware_datetime_normalizes_to_utc_and_preserves_instant() -> None:
    offset = timezone(timedelta(hours=3))
    original = datetime(2026, 7, 25, 15, 0, tzinfo=offset)

    value = build_input(observed_at=original)

    assert value.observed_at == OBSERVED_AT
    assert value.observed_at.tzinfo is timezone.utc
    assert value.observed_at.timestamp() == original.timestamp()


@pytest.mark.parametrize("threshold", [0.0, -1.0])
def test_extreme_change_percent_must_be_positive(threshold) -> None:
    with pytest.raises(
        ValueError,
        match="extreme_change_percent must be greater than 0",
    ):
        build_policy(extreme_change_percent=threshold)


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "medium_score_threshold": 25.0,
            "high_score_threshold": 25.0,
        },
        {
            "high_score_threshold": 50.0,
            "extreme_score_threshold": 50.0,
        },
        {
            "medium_score_threshold": 60.0,
            "high_score_threshold": 50.0,
        },
    ],
)
def test_invalid_threshold_ordering_is_rejected(overrides) -> None:
    with pytest.raises(ValueError, match="score thresholds must satisfy"):
        build_policy(**overrides)


def test_threshold_lower_bound_is_enforced() -> None:
    with pytest.raises(ValueError, match="score thresholds must satisfy"):
        build_policy(medium_score_threshold=-0.1)


def test_threshold_upper_bound_is_enforced() -> None:
    with pytest.raises(ValueError, match="score thresholds must satisfy"):
        build_policy(extreme_score_threshold=100.1)


def test_ten_percent_increase_uses_absolute_change_score() -> None:
    result = evaluate(
        build_input(open_interest=110.0, previous_open_interest=100.0),
        build_policy(extreme_change_percent=100.0),
    )

    assert result.score == 10.0
    assert result.reason_code == "OI_INCREASE"


def test_ten_percent_decrease_uses_absolute_change_score() -> None:
    result = evaluate(
        build_input(open_interest=90.0, previous_open_interest=100.0),
        build_policy(extreme_change_percent=100.0),
    )

    assert result.score == 10.0
    assert result.reason_code == "OI_DECREASE"


def test_equal_increase_and_decrease_magnitudes_produce_equal_scores() -> None:
    policy = build_policy(extreme_change_percent=100.0)

    increase = evaluate(build_input(open_interest=110.0), policy)
    decrease = evaluate(build_input(open_interest=90.0), policy)

    assert increase.score == decrease.score


@pytest.mark.parametrize(
    ("open_interest", "reason_code"),
    [
        (110.0, "OI_INCREASE"),
        (90.0, "OI_DECREASE"),
        (100.0, "OI_UNCHANGED"),
    ],
)
def test_change_sign_selects_reason_code(open_interest, reason_code) -> None:
    result = evaluate(
        build_input(
            open_interest=open_interest,
            previous_open_interest=100.0,
        ),
        build_policy(),
    )

    assert result.reason_code == reason_code


def test_negative_zero_change_is_unchanged() -> None:
    result = evaluate(
        build_input(open_interest=100.0, previous_open_interest=100.0),
        build_policy(),
    )

    assert result.score == 0.0
    assert result.reason_code == "OI_UNCHANGED"


def test_score_caps_at_exactly_100() -> None:
    result = evaluate(
        build_input(open_interest=200.0, previous_open_interest=100.0),
        build_policy(extreme_change_percent=10.0),
    )

    assert result.score == 100.0


@pytest.mark.parametrize(
    ("open_interest", "expected_score", "expected_level"),
    [
        (100.0, 0.0, RiskLevel.LOW),
        (125.0, 25.0, RiskLevel.MEDIUM),
        (150.0, 50.0, RiskLevel.HIGH),
        (175.0, 75.0, RiskLevel.EXTREME),
    ],
)
def test_exact_boundaries_map_upward_without_approximation(
    open_interest,
    expected_score,
    expected_level,
) -> None:
    result = evaluate(
        build_input(
            open_interest=open_interest,
            previous_open_interest=100.0,
        ),
        build_policy(extreme_change_percent=100.0),
    )

    assert result.score == expected_score
    assert result.level is expected_level


def test_value_below_medium_maps_to_low() -> None:
    result = evaluate(
        build_input(open_interest=110.0, previous_open_interest=100.0),
        build_policy(extreme_change_percent=100.0),
    )

    assert result.score == 10.0
    assert result.level is RiskLevel.LOW


def test_result_is_risk_component_with_open_interest_factor() -> None:
    result = evaluate(build_input(), build_policy())

    assert isinstance(result, RiskComponent)
    assert result.factor is RiskFactor.OPEN_INTEREST


def test_derivatives_package_exports_are_minimal_and_exact() -> None:
    assert app.risk.derivatives.__all__ == [
        "FundingRiskEvaluator",
        "FundingRiskInput",
        "FundingRiskPolicy",
        "OpenInterestRiskEvaluator",
        "OpenInterestRiskInput",
        "OpenInterestRiskPolicy",
    ]


def test_repeated_evaluation_is_deterministic() -> None:
    evaluator = OpenInterestRiskEvaluator()
    value = build_input()
    policy = build_policy()

    assert evaluator.evaluate(value, policy) == evaluator.evaluate(value, policy)


def test_evaluator_is_stateless() -> None:
    evaluator = OpenInterestRiskEvaluator()

    assert evaluator.__dict__ == {}
    evaluator.evaluate(build_input(), build_policy())
    assert evaluator.__dict__ == {}


def test_derivatives_package_has_no_intelligence_or_decision_imports() -> None:
    package_directory = Path(app.risk.derivatives.__file__).parent

    for path in package_directory.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_modules.append(node.module)

        assert not any(
            module == "app.intelligence"
            or module.startswith("app.intelligence.")
            or module == "app.decision"
            or module.startswith("app.decision.")
            for module in imported_modules
        )


def test_existing_risk_score_contract_is_unchanged() -> None:
    assert [field.name for field in fields(RiskScore)] == [
        "total_score",
        "liquidity_score",
        "funding_score",
        "whale_score",
        "flow_score",
        "volatility_score",
    ]


def test_existing_funding_evaluator_remains_compatible() -> None:
    funding_input = FundingRiskInput(
        source="normalized-funding",
        symbol="BTCUSDT",
        funding_rate=0.0003,
        funding_interval_hours=8.0,
        observed_at=OBSERVED_AT,
    )
    funding_policy = FundingRiskPolicy(
        extreme_annualized_percent=100.0,
        medium_score_threshold=25.0,
        high_score_threshold=50.0,
        extreme_score_threshold=75.0,
    )

    result = FundingRiskEvaluator().evaluate(funding_input, funding_policy)

    assert isinstance(result, RiskComponent)
    assert result.factor is RiskFactor.FUNDING
    assert result.score == pytest.approx(32.85)
    assert result.level is RiskLevel.MEDIUM
    assert result.reason_code == "FUNDING_POSITIVE"


def test_python_39_type_hints_resolve() -> None:
    assert get_type_hints(OpenInterestRiskInput) == {
        "source": str,
        "symbol": str,
        "open_interest": float,
        "previous_open_interest": float,
        "observed_at": datetime,
    }
    assert get_type_hints(OpenInterestRiskPolicy) == {
        "extreme_change_percent": float,
        "medium_score_threshold": float,
        "high_score_threshold": float,
        "extreme_score_threshold": float,
    }
    assert get_type_hints(OpenInterestRiskEvaluator.evaluate) == {
        "value": OpenInterestRiskInput,
        "policy": OpenInterestRiskPolicy,
        "return": RiskComponent,
    }
