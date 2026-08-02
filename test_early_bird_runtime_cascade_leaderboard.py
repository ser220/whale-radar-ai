from app.intelligence.early_bird.runtime import (
    EarlyBirdRuntime,
)


def test_runtime_builds_perpetual_leaderboard_flow():

    runtime = EarlyBirdRuntime()

    result = runtime.process_cascade_pipeline(
        asset="HYPE",
        long_score=85,
        short_score=20,
    )

    assert result.opportunity.asset == "HYPE"
    assert result.opportunity.direction == "LONG"
    assert result.opportunity.rank == "L4"
