import ast
import math
from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import get_type_hints

import pytest

import app.risk.derivatives
import app.risk.flow
import app.risk.liquidations
from app.risk import RiskComponent, RiskFactor, RiskLevel, RiskScore
from app.risk.derivatives import (
    FundingRiskEvaluator,
    FundingRiskInput,
    FundingRiskPolicy,
    OpenInterestRiskEvaluator,
    OpenInterestRiskInput,
    OpenInterestRiskPolicy,
)
from app.risk.flow import CVDRiskEvaluator, CVDRiskInput, CVDRiskPolicy
from app.risk.liquidations import (
    LiquidationRiskEvaluator,
    LiquidationRiskInput,
    LiquidationRiskPolicy,
)


OBSERVED_AT = datetime(
    2026,
    7,
    25,
    12,
    0,
    tzinfo=timezone.utc,
)

DERIVATIVES_EXPORTS = [
    "FundingRiskEvaluator",
    "FundingRiskInput",
    "FundingRiskPolicy",
    "OpenInterestRiskEvaluator",
    "OpenInterestRiskInput",
    "OpenInterestRiskPolicy",
]

FLOW_EXPORTS = [
    "CVDRiskEvaluator",
    "CVDRiskInput",
    "CVDRiskPolicy",
]


def build_input(**overrides) -> LiquidationRiskInput:
    values = {
        "source": "normalized-liquidations",
        "symbol": "BTCUSDT",
        "long_liquidation_notional": 10.0,
        "short_liquidation_notional": 5.0,
        "total_traded_notional": 100.0,
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return LiquidationRiskInput(**values)


def build_policy(**overrides) -> LiquidationRiskPolicy:
    values = {
        "extreme_liquidation_percent": 100.0,
        "balanced_difference_percent": 10.0,
        "medium_score_threshold": 25.0,
        "high_score_threshold": 50.0,
        "extreme_score_threshold": 75.0,
    }
    values.update(overrides)
    return LiquidationRiskPolicy(**values)


def evaluate(
    value: LiquidationRiskInput,
    policy: LiquidationRiskPolicy,
) -> RiskComponent:
    return LiquidationRiskEvaluator().evaluate(value, policy)


def test_input_fields_are_exact() -> None:
    assert [field.name for field in fields(LiquidationRiskInput)] == [
        "source",
        "symbol",
        "long_liquidation_notional",
        "short_liquidation_notional",
        "total_traded_notional",
        "observed_at",
    ]


def test_policy_fields_are_exact() -> None:
    assert [field.name for field in fields(LiquidationRiskPolicy)] == [
        "extreme_liquidation_percent",
        "balanced_difference_percent",
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
        first.long_liquidation_notional = 20.0


def test_policy_is_frozen_hashable_and_deterministic() -> None:
    first = build_policy()
    second = build_policy()

    assert first == second
    assert first is not second
    assert hash(first) == hash(second)
    assert {first, second} == {first}
    with pytest.raises(FrozenInstanceError):
        first.extreme_liquidation_percent = 50.0


def test_source_is_trimmed() -> None:
    assert build_input(source="  normalized-liq  ").source == "normalized-liq"


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
        ("input", "long_liquidation_notional"),
        ("input", "short_liquidation_notional"),
        ("input", "total_traded_notional"),
        ("policy", "extreme_liquidation_percent"),
        ("policy", "balanced_difference_percent"),
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
        ("input", "long_liquidation_notional"),
        ("input", "short_liquidation_notional"),
        ("input", "total_traded_notional"),
        ("policy", "extreme_liquidation_percent"),
        ("policy", "balanced_difference_percent"),
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


@pytest.mark.parametrize(
    "field_name",
    ["long_liquidation_notional", "short_liquidation_notional"],
)
def test_liquidation_notional_accepts_zero(field_name) -> None:
    value = build_input(**{field_name: 0.0})

    assert getattr(value, field_name) == 0.0


@pytest.mark.parametrize(
    "field_name",
    ["long_liquidation_notional", "short_liquidation_notional"],
)
def test_liquidation_notional_rejects_negative_values(field_name) -> None:
    with pytest.raises(
        ValueError,
        match=f"{field_name} must be greater than or equal to 0",
    ):
        build_input(**{field_name: -1.0})


@pytest.mark.parametrize("total_traded_notional", [0.0, -1.0])
def test_total_traded_notional_rejects_non_positive_values(
    total_traded_notional,
) -> None:
    with pytest.raises(
        ValueError,
        match="total_traded_notional must be greater than 0",
    ):
        build_input(total_traded_notional=total_traded_notional)


def test_liquidation_sum_equal_to_total_traded_notional_is_accepted() -> None:
    value = build_input(
        long_liquidation_notional=60.0,
        short_liquidation_notional=40.0,
        total_traded_notional=100.0,
    )

    assert (
        value.long_liquidation_notional
        + value.short_liquidation_notional
        == value.total_traded_notional
    )


def test_liquidation_sum_greater_than_total_traded_notional_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "total liquidation notional must be less than or equal to "
            "total_traded_notional"
        ),
    ):
        build_input(
            long_liquidation_notional=60.0,
            short_liquidation_notional=40.1,
            total_traded_notional=100.0,
        )


def test_integer_numeric_values_normalize_to_float() -> None:
    value = LiquidationRiskInput(
        source="normalized-liquidations",
        symbol="BTCUSDT",
        long_liquidation_notional=10,
        short_liquidation_notional=5,
        total_traded_notional=100,
        observed_at=OBSERVED_AT,
    )
    policy = LiquidationRiskPolicy(
        extreme_liquidation_percent=100,
        balanced_difference_percent=10,
        medium_score_threshold=25,
        high_score_threshold=50,
        extreme_score_threshold=75,
    )

    assert all(
        isinstance(getattr(value, field.name), float)
        for field in fields(LiquidationRiskInput)
        if field.name.endswith("notional")
    )
    assert all(
        isinstance(getattr(policy, field.name), float)
        for field in fields(LiquidationRiskPolicy)
    )


@pytest.mark.parametrize("zero", [0.0, -0.0])
@pytest.mark.parametrize(
    "field_name",
    ["long_liquidation_notional", "short_liquidation_notional"],
)
def test_liquidation_zero_normalizes_to_positive_zero(
    field_name,
    zero,
) -> None:
    value = build_input(**{field_name: zero})
    normalized = getattr(value, field_name)

    assert normalized == 0.0
    assert math.copysign(1.0, normalized) == 1.0


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
def test_extreme_liquidation_percent_rejects_non_positive_values(
    threshold,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "extreme_liquidation_percent must be greater than 0 "
            "and less than or equal to 100"
        ),
    ):
        build_policy(extreme_liquidation_percent=threshold)


def test_extreme_liquidation_percent_accepts_100() -> None:
    assert build_policy(
        extreme_liquidation_percent=100.0
    ).extreme_liquidation_percent == 100.0


def test_extreme_liquidation_percent_rejects_above_100() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "extreme_liquidation_percent must be greater than 0 "
            "and less than or equal to 100"
        ),
    ):
        build_policy(extreme_liquidation_percent=100.1)


@pytest.mark.parametrize("threshold", [0.0, 100.0])
def test_balanced_difference_percent_accepts_bounds(threshold) -> None:
    assert build_policy(
        balanced_difference_percent=threshold
    ).balanced_difference_percent == threshold


@pytest.mark.parametrize("threshold", [-0.1, 100.1])
def test_balanced_difference_percent_rejects_outside_bounds(threshold) -> None:
    with pytest.raises(
        ValueError,
        match="balanced_difference_percent must be between 0 and 100",
    ):
        build_policy(balanced_difference_percent=threshold)


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


def test_total_liquidation_example_produces_fifteen_percent_score() -> None:
    result = evaluate(
        build_input(
            long_liquidation_notional=10.0,
            short_liquidation_notional=5.0,
            total_traded_notional=100.0,
        ),
        build_policy(extreme_liquidation_percent=100.0),
    )

    assert result.score == 15.0


def test_swapped_long_short_values_produce_equal_scores_and_levels() -> None:
    policy = build_policy()
    long_dominant = evaluate(
        build_input(
            long_liquidation_notional=10.0,
            short_liquidation_notional=5.0,
        ),
        policy,
    )
    short_dominant = evaluate(
        build_input(
            long_liquidation_notional=5.0,
            short_liquidation_notional=10.0,
        ),
        policy,
    )

    assert long_dominant.score == short_dominant.score
    assert long_dominant.level is short_dominant.level


def test_no_liquidations_reason_code() -> None:
    result = evaluate(
        build_input(
            long_liquidation_notional=0.0,
            short_liquidation_notional=0.0,
        ),
        build_policy(),
    )

    assert result.reason_code == "LIQUIDATIONS_NONE"


def test_equal_liquidations_are_balanced() -> None:
    result = evaluate(
        build_input(
            long_liquidation_notional=10.0,
            short_liquidation_notional=10.0,
        ),
        build_policy(balanced_difference_percent=0.0),
    )

    assert result.reason_code == "LIQUIDATIONS_BALANCED"


def test_exact_balanced_difference_boundary_maps_to_balanced() -> None:
    result = evaluate(
        build_input(
            long_liquidation_notional=55.0,
            short_liquidation_notional=45.0,
        ),
        build_policy(balanced_difference_percent=10.0),
    )

    assert result.reason_code == "LIQUIDATIONS_BALANCED"


@pytest.mark.parametrize(
    ("long_notional", "short_notional", "reason_code"),
    [
        (20.0, 5.0, "LONG_LIQUIDATIONS_DOMINANT"),
        (5.0, 20.0, "SHORT_LIQUIDATIONS_DOMINANT"),
    ],
)
def test_liquidation_dominance_reason_codes(
    long_notional,
    short_notional,
    reason_code,
) -> None:
    result = evaluate(
        build_input(
            long_liquidation_notional=long_notional,
            short_liquidation_notional=short_notional,
        ),
        build_policy(),
    )

    assert result.reason_code == reason_code


def test_reason_code_does_not_alter_score_or_level() -> None:
    policy = build_policy()
    long_dominant = evaluate(
        build_input(
            long_liquidation_notional=10.0,
            short_liquidation_notional=5.0,
        ),
        policy,
    )
    short_dominant = evaluate(
        build_input(
            long_liquidation_notional=5.0,
            short_liquidation_notional=10.0,
        ),
        policy,
    )

    assert long_dominant.reason_code != short_dominant.reason_code
    assert long_dominant.score == short_dominant.score
    assert long_dominant.level is short_dominant.level


def test_score_caps_at_exactly_100() -> None:
    result = evaluate(
        build_input(
            long_liquidation_notional=50.0,
            short_liquidation_notional=50.0,
            total_traded_notional=100.0,
        ),
        build_policy(extreme_liquidation_percent=10.0),
    )

    assert result.score == 100.0


@pytest.mark.parametrize(
    ("long_notional", "expected_score", "expected_level"),
    [
        (0.0, 0.0, RiskLevel.LOW),
        (25.0, 25.0, RiskLevel.MEDIUM),
        (50.0, 50.0, RiskLevel.HIGH),
        (75.0, 75.0, RiskLevel.EXTREME),
    ],
)
def test_exact_boundaries_map_upward_without_approximation(
    long_notional,
    expected_score,
    expected_level,
) -> None:
    result = evaluate(
        build_input(
            long_liquidation_notional=long_notional,
            short_liquidation_notional=0.0,
            total_traded_notional=100.0,
        ),
        build_policy(extreme_liquidation_percent=100.0),
    )

    assert result.score == expected_score
    assert result.level is expected_level


def test_value_below_medium_maps_to_low() -> None:
    result = evaluate(
        build_input(
            long_liquidation_notional=20.0,
            short_liquidation_notional=0.0,
            total_traded_notional=100.0,
        ),
        build_policy(extreme_liquidation_percent=100.0),
    )

    assert result.score == 20.0
    assert result.level is RiskLevel.LOW


def test_result_is_risk_component_with_liquidations_factor() -> None:
    result = evaluate(build_input(), build_policy())

    assert isinstance(result, RiskComponent)
    assert result.factor is RiskFactor.LIQUIDATIONS


def test_repeated_evaluation_is_deterministic() -> None:
    evaluator = LiquidationRiskEvaluator()
    value = build_input()
    policy = build_policy()

    assert evaluator.evaluate(value, policy) == evaluator.evaluate(value, policy)


def test_evaluator_has_no_instance_state() -> None:
    evaluator = LiquidationRiskEvaluator()

    assert evaluator.__dict__ == {}
    evaluator.evaluate(build_input(), build_policy())
    assert evaluator.__dict__ == {}


def test_liquidations_package_exports_are_minimal_and_exact() -> None:
    assert app.risk.liquidations.__all__ == [
        "LiquidationRiskEvaluator",
        "LiquidationRiskInput",
        "LiquidationRiskPolicy",
    ]


def test_liquidations_package_has_no_intelligence_or_decision_imports() -> None:
    package_directory = Path(app.risk.liquidations.__file__).parent

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
    result = FundingRiskEvaluator().evaluate(
        FundingRiskInput(
            source="normalized-funding",
            symbol="BTCUSDT",
            funding_rate=0.0003,
            funding_interval_hours=8.0,
            observed_at=OBSERVED_AT,
        ),
        FundingRiskPolicy(
            extreme_annualized_percent=100.0,
            medium_score_threshold=25.0,
            high_score_threshold=50.0,
            extreme_score_threshold=75.0,
        ),
    )

    assert result.factor is RiskFactor.FUNDING
    assert result.score == pytest.approx(32.85)
    assert result.level is RiskLevel.MEDIUM
    assert result.reason_code == "FUNDING_POSITIVE"


def test_existing_open_interest_evaluator_remains_compatible() -> None:
    result = OpenInterestRiskEvaluator().evaluate(
        OpenInterestRiskInput(
            source="normalized-open-interest",
            symbol="BTCUSDT",
            open_interest=110.0,
            previous_open_interest=100.0,
            observed_at=OBSERVED_AT,
        ),
        OpenInterestRiskPolicy(
            extreme_change_percent=100.0,
            medium_score_threshold=25.0,
            high_score_threshold=50.0,
            extreme_score_threshold=75.0,
        ),
    )

    assert result.factor is RiskFactor.OPEN_INTEREST
    assert result.score == 10.0
    assert result.level is RiskLevel.LOW
    assert result.reason_code == "OI_INCREASE"


def test_existing_cvd_evaluator_remains_compatible() -> None:
    result = CVDRiskEvaluator().evaluate(
        CVDRiskInput(
            source="normalized-cvd",
            symbol="BTCUSDT",
            cvd_delta=20.0,
            total_volume=100.0,
            observed_at=OBSERVED_AT,
        ),
        CVDRiskPolicy(
            extreme_imbalance_percent=100.0,
            medium_score_threshold=25.0,
            high_score_threshold=50.0,
            extreme_score_threshold=75.0,
        ),
    )

    assert result.factor is RiskFactor.CVD
    assert result.score == 20.0
    assert result.level is RiskLevel.LOW
    assert result.reason_code == "CVD_BUY_DOMINANT"


def test_existing_package_exports_remain_unchanged() -> None:
    assert app.risk.derivatives.__all__ == DERIVATIVES_EXPORTS
    assert app.risk.flow.__all__ == FLOW_EXPORTS


def test_python_39_type_hints_resolve() -> None:
    assert get_type_hints(LiquidationRiskInput) == {
        "source": str,
        "symbol": str,
        "long_liquidation_notional": float,
        "short_liquidation_notional": float,
        "total_traded_notional": float,
        "observed_at": datetime,
    }
    assert get_type_hints(LiquidationRiskPolicy) == {
        "extreme_liquidation_percent": float,
        "balanced_difference_percent": float,
        "medium_score_threshold": float,
        "high_score_threshold": float,
        "extreme_score_threshold": float,
    }
    assert get_type_hints(LiquidationRiskEvaluator.evaluate) == {
        "value": LiquidationRiskInput,
        "policy": LiquidationRiskPolicy,
        "return": RiskComponent,
    }
