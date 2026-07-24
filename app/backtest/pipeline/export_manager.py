from pathlib import Path

from app.backtest.pipeline.json_file_writer import (
    BacktestPipelineJSONFileWriter,
)
from app.backtest.pipeline.models import (
    BacktestPipelineResult,
)
from app.backtest.pipeline.timestamped_json_writer import (
    BacktestPipelineTimestampedJSONWriter,
)

from typing import Optional

class BacktestPipelineExportManager:
    """
    Coordinates backtest pipeline exports.

    Provides a single entry point for exporting
    completed pipeline results.
    """

    def __init__(
        self,
        file_writer: Optional[BacktestPipelineJSONFileWriter] = None,
        timestamped_writer: Optional[BacktestPipelineTimestampedJSONWriter] = None,
    ) -> None:
        self.file_writer = (
            file_writer
            if file_writer is not None
            else BacktestPipelineJSONFileWriter()
        )

        self.timestamped_writer = (
            timestamped_writer
            if timestamped_writer is not None
            else BacktestPipelineTimestampedJSONWriter()
        )

    def export_json(
        self,
        result: BacktestPipelineResult,
        path: Path,
    ) -> Path:
        return self.file_writer.write(
            result=result,
            output_file=path,
        )

    def export_timestamped_json(
        self,
        result: BacktestPipelineResult,
        output_directory: Path,
    ) -> Path:
        return self.timestamped_writer.write(
            result=result,
            output_directory=output_directory,
        )
