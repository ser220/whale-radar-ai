from pathlib import Path
from typing import Optional

from app.backtest.pipeline.json_exporter import (
    BacktestPipelineJSONExporter,
)
from app.backtest.pipeline.models import (
    BacktestPipelineResult,
)


class BacktestPipelineJSONFileWriter:
    """
    Writes a serialized backtest pipeline result
    to a JSON file.
    """

    def __init__(
        self,
        exporter: Optional[
            BacktestPipelineJSONExporter
        ] = None,
    ) -> None:
        self._exporter = (
            exporter
            if exporter is not None
            else BacktestPipelineJSONExporter()
        )

    def write(
        self,
        result: BacktestPipelineResult,
        output_file: Path,
    ) -> Path:
        exported_json = self._exporter.export(result)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file.write_text(
            exported_json,
            encoding="utf-8",
        )

        return output_file
