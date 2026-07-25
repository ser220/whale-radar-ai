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
)


OBSERVED_AT = datetime(
    2026,
    7,
    25,
    12,
    0,
    tzinfo=timezone.utc,
)


def build_input(**overrides) -> FundingRiskInput:
    values = {
        "source": "normalized-funding",
        "symbol": "BTCUSDT",
        "funding_rate": 0.0003,
        "funding_interval_hours": 8.0,
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return FundingRiskInput(**values)


def build_policy(**overrides) -> FundingRiskPolicy:
    values = {
        "extreme_annualized_percent": 100.0,
        "medium_score_threshold": 25.0,
        "high_score_threshold": 50.0,
        "extreme_score_threshold": 75.0,
    }
    values.update(overrides)
    return FundingRiskPolicy(**values)


def evaluate(
    funding_input: FundingRiskInput,
    policy: FundingRiskPolicy = None,
) -> RiskComponent:
    return FundingRiskEvaluator().evaluate(
        funding_input,
        policy if policy is not None else build_policy(),
    )


def test_funding_risk_input_fields_are_exact() -> None:
    assert [field.name for field in fields(FundingRiskInput)] == [
        "source",
        "symbol",
        "funding_rate",
        "funding_interval_hours",
        "observed_at",
    ]


def test_funding_risk_policy_fields_are_exact() -> None:
    assert [field.name for field in fields(FundingRiskPolicy)] == [
        "extreme_annualized_percent",
        "medium_score_threshold",
        "high_score_threshold",
        "extreme_score_threshold",
    ]


def test_input_is_immutable_and_hashable() -> None:
    value = build_input()
    equal_value = build_input()

    assert value == equal_value
    assert hash(value) == hash(equal_value)
    assert {value, equal_value} == {value}
    with pytest.raises(FrozenInstanceError):
        value.funding_rate = 0.5


def test_policy_is_immutable_and_hashable() -> None:
    policy = build_policy()
    equal_policy = build_policy()

    assert policy == equal_policy
    assert hash(policy) == hash(equal_policy)
    assert {policy, equal_policy} == {policy}
    with pytest.raises(FrozenInstanceError):
        policy.extreme_annualized_percent = 1.0


def test_aware_timestamp_normalizes_to_utc() -> None:
    offset = timezone(timedelta(hours=3))
    value = build_input(
        observed_at=datetime(2026, 7, 25, 15, 0, tzinfo=offset)
    )

    assert value.observed_at == OBSERVED_AT
    assert value.observed_at.tzinfo is timezone.utc


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        build_input(observed_at=datetime(2026, 7, 25, 12, 0))


@pytest.mark.parametrize("source", ["", " ", "\t\n"])
def test_empty_source_is_rejected(source) -> None:
    with pytest.raises(ValueError, match="source must not be empty"):
        build_input(source=source)


@pytest.mark.parametrize("symbol", ["", " ", "\t\n"])
def test_empty_symbol_is_rejected(symbol) -> None:
    with pytest.raises(ValueError, match="symbol must not be empty"):
        build_input(symbol=symbol)


@pytest.mark.parametrize(
    ("target", "field_name"),
    [
        ("input", "funding_rate"),
        ("input", "funding_interval_hours"),
        ("policy", "extreme_annualized_percent"),
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
        ("input", "funding_rate"),
        ("input", "funding_interval_hours"),
        ("policy", "extreme_annualized_percent"),
        ("policy", "medium_score_threshold"),
        ("policy", "high_score_threshold"),
        ("policy", "extreme_score_threshold"),
    ],
)
def test_non_finite_numbers_are_rejected(target, field_name, invalid) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must be finite"):
        if target == "input":
            build_input(**{field_name: invalid})
        else:
            build_policy(**{field_name: invalid})


@pytest.mark.parametrize("interval", [0.0, -1.0])
def test_non_positive_funding_interval_is_rejected(interval) -> None:
    with pytest.raises(
        ValueError,
        match="funding_interval_hours must be greater than 0",
    ):
        build_input(funding_interval_hours=interval)


@pytest.mark.parametrize("threshold", [0.0, -1.0])
def test_non_positive_extreme_annualized_threshold_is_rejected(
    threshold,
) -> None:
    with pytest.raises(
        ValueError,
        match="extreme_annualized_percent must be greater than 0",
    ):
        build_policy(extreme_annualized_percent=threshold)


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
def test_invalid_score_threshold_ordering_is_rejected(overrides) -> None:
    with pytest.raises(ValueError, match="score thresholds must satisfy"):
        build_policy(**overrides)


@pytest.mark.parametrize(
    "overrides",
    [
        {"medium_score_threshold": -0.1},
        {"extreme_score_threshold": 100.1},
    ],
)
def test_score_thresholds_outside_range_are_rejected(overrides) -> None:
    with pytest.raises(ValueError, match="score thresholds must satisfy"):
        build_policy(**overrides)


def test_annualization_example_produces_32_85_percent_score() -> None:
    result = evaluate(
        build_input(
            funding_rate=0.0003,
            funding_interval_hours=8.0,
        )
    )

    assert result.score == pytest.approx(32.85)


def test_equal_positive_and_negative_magnitudes_produce_equal_scores() -> None:
    positive = evaluate(build_input(funding_rate=0.0003))
    negative = evaluate(build_input(funding_rate=-0.0003))

    assert positive.score == negative.score


@pytest.mark.parametrize(
    ("funding_rate", "reason_code"),
    [
        (0.0003, "FUNDING_POSITIVE"),
        (-0.0003, "FUNDING_NEGATIVE"),
        (0.0, "FUNDING_NEUTRAL"),
    ],
)
def test_funding_sign_selects_reason_code(
    funding_rate,
    reason_code,
) -> None:
    result = evaluate(build_input(funding_rate=funding_rate))

    assert result.reason_code == reason_code


def test_score_caps_exactly_at_100() -> None:
    result = evaluate(build_input(funding_rate=1.0))

    assert result.score == 100.0


@pytest.mark.parametrize(
    ("funding_rate", "expected_score", "expected_level"),
    [
        (0.0, 0.0, RiskLevel.LOW),
        (0.25, 25.0, RiskLevel.MEDIUM),
        (0.5, 50.0, RiskLevel.HIGH),
        (0.75, 75.0, RiskLevel.EXTREME),
    ],
)
def test_exact_configured_score_boundaries_map_inclusively(
    funding_rate,
    expected_score,
    expected_level,
) -> None:
    policy = build_policy(extreme_annualized_percent=36500.0)

    result = evaluate(
        build_input(
            funding_rate=funding_rate,
            funding_interval_hours=24.0,
        ),
        policy,
    )

    assert result.score == expected_score
    assert result.level is expected_level


def test_repeated_evaluation_produces_equal_results() -> None:
    evaluator = FundingRiskEvaluator()
    value = build_input()
    policy = build_policy()

    assert evaluator.evaluate(value, policy) == evaluator.evaluate(value, policy)


def test_result_factor_is_funding() -> None:
    result = evaluate(build_input())

    assert result.factor is RiskFactor.FUNDING


def test_existing_risk_score_contract_is_unchanged() -> None:
    assert [field.name for field in fields(RiskScore)] == [
        "total_score",
        "liquidity_score",
        "funding_score",
        "whale_score",
        "flow_score",
        "volatility_score",
    ]


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


def test_python_39_type_hints_resolve() -> None:
    assert get_type_hints(FundingRiskInput) == {
        "source": str,
        "symbol": str,
        "funding_rate": float,
        "funding_interval_hours": float,
        "observed_at": datetime,
    }
    assert get_type_hints(FundingRiskPolicy) == {
        "extreme_annualized_percent": float,
        "medium_score_threshold": float,
        "high_score_threshold": float,
        "extreme_score_threshold": float,
    }
    assert get_type_hints(FundingRiskEvaluator.evaluate) == {
        "value": FundingRiskInput,
        "policy": FundingRiskPolicy,
        "return": RiskComponent,
    }
