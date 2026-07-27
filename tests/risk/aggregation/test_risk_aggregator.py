from dataclasses import FrozenInstanceError

import pytest

from app.risk import RiskComponent, RiskFactor, RiskLevel
from app.risk.aggregation import (
    AggregatedRiskScore,
    RiskAggregationPolicy,
    RiskAggregator,
)


def build_policy(**overrides) -> RiskAggregationPolicy:
    weights = {
        factor: 0.0
        for factor in RiskFactor
    }
    weights.update(
        {
            RiskFactor.FUNDING: 2.0,
            RiskFactor.CVD: 1.0,
            RiskFactor.LIQUIDATIONS: 1.0,
        }
    )

    supplied_weights = overrides.pop("weights", None)

    if supplied_weights is not None:
        weights = {
            factor: 0.0
            for factor in RiskFactor
        }
        weights.update(supplied_weights)

    values = {
        "weights": weights,
        "medium_score_threshold": 25.0,
        "high_score_threshold": 50.0,
        "extreme_score_threshold": 75.0,
    }
    values.update(overrides)

    return RiskAggregationPolicy(**values)


def build_component(
    factor: RiskFactor,
    score: float,
) -> RiskComponent:
    return RiskComponent(
        factor=factor,
        score=score,
        level=RiskLevel.LOW,
        reason_code="TEST",
    )


def test_weighted_average_is_calculated_correctly() -> None:
    result = RiskAggregator().aggregate(
        [
            build_component(RiskFactor.FUNDING, 100.0),
            build_component(RiskFactor.CVD, 50.0),
            build_component(RiskFactor.LIQUIDATIONS, 0.0),
        ],
        build_policy(),
    )

    assert result.total_score == 62.5
    assert result.level is RiskLevel.HIGH


@pytest.mark.parametrize(
    ("score", "expected_level"),
    [
        (0.0, RiskLevel.LOW),
        (24.9, RiskLevel.LOW),
        (25.0, RiskLevel.MEDIUM),
        (49.9, RiskLevel.MEDIUM),
        (50.0, RiskLevel.HIGH),
        (74.9, RiskLevel.HIGH),
        (75.0, RiskLevel.EXTREME),
        (100.0, RiskLevel.EXTREME),
    ],
)
def test_score_thresholds_resolve_expected_level(
    score,
    expected_level,
) -> None:
    policy = build_policy(
        weights={RiskFactor.FUNDING: 1.0},
    )

    result = RiskAggregator().aggregate(
        [build_component(RiskFactor.FUNDING, score)],
        policy,
    )

    assert result.level is expected_level


def test_zero_weight_component_is_ignored() -> None:
    policy = build_policy(
        weights={
            RiskFactor.FUNDING: 1.0,
            RiskFactor.CVD: 0.0,
        },
    )

    result = RiskAggregator().aggregate(
        [
            build_component(RiskFactor.FUNDING, 40.0),
            build_component(RiskFactor.CVD, 100.0),
        ],
        policy,
    )

    assert result.total_score == 40.0
    assert result.level is RiskLevel.MEDIUM


def test_components_are_sorted_by_risk_factor_value() -> None:
    funding_component = build_component(
        RiskFactor.FUNDING,
        40.0,
    )
    cvd_component = build_component(
        RiskFactor.CVD,
        20.0,
    )

    policy = build_policy(
        weights={
            RiskFactor.CVD: 1.0,
            RiskFactor.FUNDING: 1.0,
        },
    )

    result = RiskAggregator().aggregate(
        [
            funding_component,
            cvd_component,
        ],
        policy,
    )

    assert isinstance(result.components, tuple)
    assert result.components == (
        cvd_component,
        funding_component,
    )


def test_generator_input_is_supported() -> None:
    policy = build_policy(
        weights={
            RiskFactor.FUNDING: 1.0,
            RiskFactor.CVD: 1.0,
        },
    )

    components = (
        build_component(factor, score)
        for factor, score in (
            (RiskFactor.FUNDING, 20.0),
            (RiskFactor.CVD, 40.0),
        )
    )

    result = RiskAggregator().aggregate(
        components,
        policy,
    )

    assert result.total_score == 30.0


def test_empty_components_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="At least one risk component is required",
    ):
        RiskAggregator().aggregate(
            [],
            build_policy(),
        )


def test_invalid_component_type_is_rejected_before_sorting() -> None:
    with pytest.raises(
        TypeError,
        match="All aggregation components must be RiskComponent",
    ):
        RiskAggregator().aggregate(
            [object()],
            build_policy(),
        )


def test_duplicate_factors_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Duplicate risk factor: FUNDING",
    ):
        RiskAggregator().aggregate(
            [
                build_component(RiskFactor.FUNDING, 20.0),
                build_component(RiskFactor.FUNDING, 40.0),
            ],
            build_policy(),
        )


def test_all_active_component_weights_equal_to_zero_are_rejected() -> None:
    policy = build_policy(
        weights={
            RiskFactor.FUNDING: 0.0,
            RiskFactor.CVD: 1.0,
        },
    )

    with pytest.raises(
        ValueError,
        match="At least one component must have a positive active weight",
    ):
        RiskAggregator().aggregate(
            [build_component(RiskFactor.FUNDING, 50.0)],
            policy,
        )


def test_policy_requires_weight_for_every_risk_factor() -> None:
    with pytest.raises(
        ValueError,
        match="Missing aggregation weights for:",
    ):
        RiskAggregationPolicy(
            weights={
                RiskFactor.FUNDING: 1.0,
            },
            medium_score_threshold=25.0,
            high_score_threshold=50.0,
            extreme_score_threshold=75.0,
        )


def test_policy_copies_and_protects_weight_mapping() -> None:
    weights = {
        factor: 0.0
        for factor in RiskFactor
    }
    weights[RiskFactor.FUNDING] = 1.0

    policy = RiskAggregationPolicy(
        weights=weights,
        medium_score_threshold=25.0,
        high_score_threshold=50.0,
        extreme_score_threshold=75.0,
    )

    weights[RiskFactor.FUNDING] = 5.0

    assert policy.weights[RiskFactor.FUNDING] == 1.0

    with pytest.raises(TypeError):
        policy.weights[RiskFactor.FUNDING] = 2.0


def test_policy_normalizes_integer_values_to_float() -> None:
    weights = {
        factor: 0
        for factor in RiskFactor
    }
    weights[RiskFactor.FUNDING] = 2

    policy = RiskAggregationPolicy(
        weights=weights,
        medium_score_threshold=25,
        high_score_threshold=50,
        extreme_score_threshold=75,
    )

    assert policy.weights[RiskFactor.FUNDING] == 2.0
    assert isinstance(
        policy.weights[RiskFactor.FUNDING],
        float,
    )
    assert isinstance(
        policy.medium_score_threshold,
        float,
    )
    assert isinstance(
        policy.high_score_threshold,
        float,
    )
    assert isinstance(
        policy.extreme_score_threshold,
        float,
    )


def test_policy_is_frozen() -> None:
    policy = build_policy()

    with pytest.raises(FrozenInstanceError):
        policy.high_score_threshold = 60.0


@pytest.mark.parametrize(
    "invalid",
    [True, False, "1", None],
)
def test_invalid_weight_type_is_rejected(invalid) -> None:
    with pytest.raises(
        TypeError,
        match="must be a real number",
    ):
        build_policy(
            weights={RiskFactor.FUNDING: invalid},
        )


@pytest.mark.parametrize(
    "invalid",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_non_finite_weight_is_rejected(invalid) -> None:
    with pytest.raises(
        ValueError,
        match="must be finite",
    ):
        build_policy(
            weights={RiskFactor.FUNDING: invalid},
        )


def test_negative_weight_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        build_policy(
            weights={RiskFactor.FUNDING: -0.1},
        )


def test_empty_weight_mapping_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="At least one aggregation weight must be greater than zero",
    ):
        build_policy(weights={})


def test_policy_with_only_zero_weights_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="At least one aggregation weight must be greater than zero",
    ):
        build_policy(
            weights={
                RiskFactor.FUNDING: 0.0,
                RiskFactor.CVD: 0.0,
            },
        )


def test_invalid_weight_key_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="All weight keys must be RiskFactor",
    ):
        RiskAggregationPolicy(
            weights={"FUNDING": 1.0},
            medium_score_threshold=25.0,
            high_score_threshold=50.0,
            extreme_score_threshold=75.0,
        )

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
            "medium_score_threshold": -0.1,
        },
        {
            "extreme_score_threshold": 100.1,
        },
    ],
)
def test_invalid_threshold_ordering_or_range_is_rejected(
    overrides,
) -> None:
    with pytest.raises(
        ValueError,
        match="Thresholds must satisfy",
    ):
        build_policy(**overrides)


def test_aggregated_result_normalizes_and_copies_components() -> None:
    source_components = [
        build_component(
            RiskFactor.FUNDING,
            50.0,
        )
    ]

    result = AggregatedRiskScore(
        total_score=50,
        level=RiskLevel.HIGH,
        components=source_components,
    )

    source_components.clear()

    assert result.total_score == 50.0
    assert isinstance(result.total_score, float)
    assert isinstance(result.components, tuple)
    assert len(result.components) == 1


def test_aggregated_result_sorts_components() -> None:
    funding_component = build_component(
        RiskFactor.FUNDING,
        50.0,
    )
    cvd_component = build_component(
        RiskFactor.CVD,
        50.0,
    )

    result = AggregatedRiskScore(
        total_score=50.0,
        level=RiskLevel.HIGH,
        components=[
            funding_component,
            cvd_component,
        ],
    )

    assert result.components == (
        cvd_component,
        funding_component,
    )


def test_aggregated_result_rejects_empty_components() -> None:
    with pytest.raises(
        ValueError,
        match="At least one risk component is required",
    ):
        AggregatedRiskScore(
            total_score=50.0,
            level=RiskLevel.HIGH,
            components=(),
        )


def test_aggregated_result_rejects_invalid_component_type() -> None:
    with pytest.raises(
        TypeError,
        match="All components must be RiskComponent",
    ):
        AggregatedRiskScore(
            total_score=50.0,
            level=RiskLevel.HIGH,
            components=[object()],
        )


def test_aggregated_result_rejects_duplicate_factors() -> None:
    with pytest.raises(
        ValueError,
        match="Duplicate risk factor: FUNDING",
    ):
        AggregatedRiskScore(
            total_score=50.0,
            level=RiskLevel.HIGH,
            components=[
                build_component(RiskFactor.FUNDING, 20.0),
                build_component(RiskFactor.FUNDING, 40.0),
            ],
        )


@pytest.mark.parametrize(
    "invalid_score",
    [
        -0.1,
        100.1,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_aggregated_result_rejects_invalid_score(
    invalid_score,
) -> None:
    with pytest.raises(ValueError):
        AggregatedRiskScore(
            total_score=invalid_score,
            level=RiskLevel.HIGH,
            components=[
                build_component(
                    RiskFactor.FUNDING,
                    50.0,
                )
            ],
        )


def test_aggregated_result_rejects_invalid_level() -> None:
    with pytest.raises(
        TypeError,
        match="level must be RiskLevel",
    ):
        AggregatedRiskScore(
            total_score=50.0,
            level="HIGH",
            components=[
                build_component(
                    RiskFactor.FUNDING,
                    50.0,
                )
            ],
        )


def test_aggregated_result_is_frozen() -> None:
    result = AggregatedRiskScore(
        total_score=50.0,
        level=RiskLevel.HIGH,
        components=[
            build_component(
                RiskFactor.FUNDING,
                50.0,
            )
        ],
    )

    with pytest.raises(FrozenInstanceError):
        result.total_score = 10.0
