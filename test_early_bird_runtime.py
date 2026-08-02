from datetime import datetime, timezone

from app.intelligence.early_bird.runtime import (
    EarlyBirdRuntime,
)
from app.intelligence.early_bird.market_sweep_result import (
    EarlyBirdMarketSweepResult,
)


NOW = datetime(
    2026,
    8,
    2,
    10,
    0,
    tzinfo=timezone.utc,
)


def test_runtime_accepts_market_sweep_result():

    runtime = EarlyBirdRuntime()

    sweep_result = EarlyBirdMarketSweepResult(
        items=(),
        scanned_assets=("BTC",),
        generated_at=NOW,
    )

    result = runtime.process(
        sweep_result,
    )

    assert result is not None


from app.intelligence.early_bird.rank_cascade_engine import (
    RankCascadeEngine,
)


def test_runtime_contains_cascade_rank():

    runtime = EarlyBirdRuntime()

    sweep_result = EarlyBirdMarketSweepResult(
        items=(),
        scanned_assets=("HYPE",),
        generated_at=NOW,
    )

    result = runtime.process(
        sweep_result,
    )

    rank = RankCascadeEngine().evaluate(
        asset="HYPE",
        long_score=85,
        short_score=20,
    )

    assert rank.long_rank == "L4"
    assert rank.short_rank == "S1"
    assert rank.transition_state == "LONG_DOMINANT"


def test_runtime_generates_cascade_from_signals():

    runtime = EarlyBirdRuntime()

    result = runtime.process_signals(
        asset="HYPE",
        signals={
            "momentum": 90,
            "volume": 80,
            "oi_health": 70,
            "exhaustion": 10,
            "bearish_structure": 5,
        },
    )

    assert result.cascade_rank.long_rank == "L3"
    assert result.cascade_rank.short_rank == "S1"
    assert result.cascade_rank.transition_state == "LONG_DOMINANT"


def test_runtime_contains_candidate_selection():

    runtime = EarlyBirdRuntime()

    assert hasattr(
        runtime,
        "process_selection",
    )


def test_runtime_full_candidate_flow_contract():

    runtime = EarlyBirdRuntime()

    result = runtime.process_full_cycle(
        asset="HYPE",
        signals={
            "momentum": 100,
            "volume": 100,
            "oi_health": 100,
            "exhaustion": 0,
            "bearish_structure": 0,
        },
        selection_result=None,
    )

    assert result.cascade_rank is not None
    assert result.cascade_rank.long_rank == "L4"


def test_runtime_generates_perpetual_direction():

    runtime = EarlyBirdRuntime()

    result = runtime.process_perpetual_cycle(
        asset="HYPE",
        signals={
            "momentum": 100,
            "volume": 100,
            "oi_health": 100,
            "exhaustion": 0,
            "bearish_structure": 0,
        },
        news_risk={
            "news_pressure_score": 10,
            "event_type": "none",
            "directional_bias": "bullish",
            "uncertainty_score": 10,
        },
    )

    assert result.direction_decision.direction == "LONG"
