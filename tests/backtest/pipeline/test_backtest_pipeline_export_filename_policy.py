from pathlib import Path

import pytest

from app.backtest.pipeline import (
    BacktestPipelineExportFilenamePolicy,
)


def test_export_filename_policy_preserves_valid_strategy_id() -> None:
    policy = BacktestPipelineExportFilenamePolicy()

    filename = policy.build_filename(
        strategy_id="Strategy Alpha_1.0",
        timestamp="20260724T120000Z",
    )

    assert filename == (
        "Strategy Alpha_1.0-20260724T120000Z.json"
    )


@pytest.mark.parametrize(
    "strategy_id",
    [
        "../strategy",
        "folder/strategy",
        "folder\\strategy",
        ".",
        "..",
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_export_filename_policy_rejects_unsafe_components(
    strategy_id: str,
) -> None:
    policy = BacktestPipelineExportFilenamePolicy()

    with pytest.raises(ValueError):
        policy.build_filename(
            strategy_id=strategy_id,
            timestamp="20260724T120000Z",
        )


@pytest.mark.parametrize(
    "strategy_id",
    [
        "/absolute/strategy",
        "C:\\absolute\\strategy",
        "\\\\server\\share\\strategy",
    ],
)
def test_export_filename_policy_rejects_absolute_paths(
    strategy_id: str,
) -> None:
    policy = BacktestPipelineExportFilenamePolicy()

    with pytest.raises(ValueError):
        policy.build_filename(
            strategy_id=strategy_id,
            timestamp="20260724T120000Z",
        )


def test_export_filename_policy_rejects_nul() -> None:
    policy = BacktestPipelineExportFilenamePolicy()

    with pytest.raises(ValueError):
        policy.build_filename(
            strategy_id="strategy\x00id",
            timestamp="20260724T120000Z",
        )


@pytest.mark.parametrize(
    "control_character",
    [chr(value) for value in range(32)] + [chr(127)],
)
def test_export_filename_policy_rejects_all_ascii_control_characters(
    control_character: str,
) -> None:
    policy = BacktestPipelineExportFilenamePolicy()

    with pytest.raises(ValueError):
        policy.build_filename(
            strategy_id=(
                f"strategy{control_character}id"
            ),
            timestamp="20260724T120000Z",
        )


def test_export_filename_policy_rejection_has_no_filesystem_effect(
    tmp_path: Path,
) -> None:
    policy = BacktestPipelineExportFilenamePolicy()
    output_directory = tmp_path / "exports"

    with pytest.raises(ValueError):
        filename = policy.build_filename(
            strategy_id="../strategy",
            timestamp="20260724T120000Z",
        )
        (output_directory / filename).write_text(
            "unexpected",
            encoding="utf-8",
        )

    assert not output_directory.exists()
    assert list(tmp_path.rglob("*")) == []
