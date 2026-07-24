from datetime import datetime, timezone

from app.simulation import (
    SimulationResult,
    SimulationRunner,
    SimulationSnapshot,
    SimulationStrategyAdapter,
)


class AlwaysBuyStrategy(
    SimulationStrategyAdapter
):
    def should_open_trade(
        self,
        snapshot,
    ) -> bool:
        return True


class FalsySelectiveStrategy(
    SimulationStrategyAdapter
):
    def __init__(self) -> None:
        self.received_snapshots = []

    def __bool__(self) -> bool:
        return False

    def should_open_trade(
        self,
        snapshot,
    ) -> bool:
        self.received_snapshots.append(
            snapshot
        )
        return snapshot.price >= 66000.0


def build_snapshot(
    price: float,
) -> SimulationSnapshot:
    return SimulationSnapshot(
        symbol="BTCUSDT",
        price=price,
        volume_24h=1000000000.0,
        volatility=0.03,
        timestamp=datetime(
            2026,
            7,
            24,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )


def test_simulation_generates_paper_trades():

    snapshots = [
        SimulationSnapshot(
            symbol="BTCUSDT",
            price=65000.0,
            volume_24h=1000000000.0,
            volatility=0.03,
            timestamp=datetime.now(
                timezone.utc
            ),
        ),
        SimulationSnapshot(
            symbol="BTCUSDT",
            price=66000.0,
            volume_24h=1000000000.0,
            volatility=0.03,
            timestamp=datetime.now(
                timezone.utc
            ),
        ),
    ]

    runner = SimulationRunner(
        strategy=AlwaysBuyStrategy()
    )

    result = runner.run(
        snapshots
    )

    assert (
        result.processed_snapshots
        == 2
    )

    assert (
        result.generated_trades
        == 2
    )


def test_simulation_invokes_injected_falsy_strategy() -> None:
    snapshots = [
        build_snapshot(
            65000.0
        ),
        build_snapshot(
            66000.0
        ),
    ]
    strategy = FalsySelectiveStrategy()

    result = SimulationRunner(
        strategy=strategy,
    ).run(
        snapshots
    )

    assert isinstance(
        result,
        SimulationResult,
    )
    assert len(
        strategy.received_snapshots
    ) == 2
    assert (
        strategy.received_snapshots[0]
        is snapshots[0]
    )
    assert (
        strategy.received_snapshots[1]
        is snapshots[1]
    )
    assert result.processed_snapshots == 2
    assert result.generated_trades == 1


def test_simulation_explicit_none_uses_default_strategy() -> None:
    snapshots = [
        build_snapshot(
            65000.0
        ),
        build_snapshot(
            66000.0
        ),
    ]

    result = SimulationRunner(
        strategy=None,
    ).run(
        snapshots
    )

    assert isinstance(
        result,
        SimulationResult,
    )
    assert result.processed_snapshots == 2
    assert result.generated_trades == 0
