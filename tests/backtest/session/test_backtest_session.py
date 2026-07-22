from datetime import datetime, timezone

from app.backtest import (
    BacktestSessionConfig,
    BacktestSessionResult,
    BacktestSessionService,
)

from app.simulation import (
    SimulationResult,
    SimulationSnapshot,
)


def build_config() -> BacktestSessionConfig:

    now = datetime.now(
        timezone.utc
    )

    return BacktestSessionConfig(
        symbol="BTCUSDT",
        start_time=now,
        end_time=now,
        initial_balance=10000.0,
    )


def test_backtest_session_result_model():

    started = datetime.now(
        timezone.utc
    )

    finished = datetime.now(
        timezone.utc
    )

    result = BacktestSessionResult(
        config=build_config(),
        processed_snapshots=10,
        generated_trades=3,
        started_at=started,
        finished_at=finished,
    )

    assert (
        result.processed_snapshots
        == 10
    )

    assert (
        result.generated_trades
        == 3
    )

    assert (
        result.config.symbol
        == "BTCUSDT"
    )


def test_simulation_result_contract():

    simulation_result = SimulationResult(
        processed_snapshots=5,
        generated_trades=2,
    )

    assert (
        simulation_result.processed_snapshots
        == 5
    )


def test_backtest_session_runs_simulation():

    snapshot = SimulationSnapshot(
        symbol="BTCUSDT",
        price=65000.0,
        volume_24h=1000000000.0,
        volatility=0.03,
        timestamp=datetime.now(
            timezone.utc
        ),
    )

    service = BacktestSessionService()

    result = service.run(
        build_config(),
        [
            snapshot,
        ],
    )

    assert (
        result.processed_snapshots
        == 1
    )

    assert (
        result.config.symbol
        == "BTCUSDT"
    )

    assert (
        result.started_at
        <= result.finished_at
    )
