from datetime import datetime, timezone

import pytest

from app.simulation import (
    SimulationResult,
    SimulationRunner,
    SimulationSnapshot,
)


def create_snapshot(
    price: float,
):
    return SimulationSnapshot(
        symbol="BTCUSDT",
        price=price,
        volume_24h=1000000000.0,
        volatility=0.03,
        timestamp=datetime.now(
            timezone.utc
        ),
    )


def test_snapshot_creation():
    snapshot = create_snapshot(
        65000.0
    )

    assert (
        snapshot.symbol
        == "BTCUSDT"
    )

    assert (
        snapshot.price
        == 65000.0
    )


def test_simulation_runner_processes_snapshots():
    runner = SimulationRunner()

    result = runner.run(
        [
            create_snapshot(65000.0),
            create_snapshot(66000.0),
            create_snapshot(67000.0),
        ]
    )

    assert isinstance(
        result,
        SimulationResult,
    )

    assert (
        result.processed_snapshots
        == 3
    )

    assert (
        result.generated_trades
        == 0
    )


def test_empty_simulation():
    runner = SimulationRunner()

    result = runner.run([])

    assert (
        result.processed_snapshots
        == 0
    )


def test_invalid_snapshot_rejected():
    runner = SimulationRunner()

    with pytest.raises(TypeError):
        runner.run(
            [
                "invalid"
            ]
        )
