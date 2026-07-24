import os
import tempfile
from pathlib import Path
from typing import Optional, TextIO

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

        temporary_file: Optional[TextIO] = None
        temporary_path: Optional[Path] = None

        try:
            temporary_file = tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=str(output_file.parent),
                prefix=f".{output_file.name}.",
                suffix=".tmp",
                delete=False,
            )
            temporary_path = Path(
                temporary_file.name
            )

            try:
                temporary_file.write(
                    exported_json
                )
                temporary_file.flush()
            except BaseException:
                try:
                    temporary_file.close()
                except BaseException:
                    pass
                raise

            temporary_file.close()

            os.replace(
                temporary_path,
                output_file,
            )
        except BaseException:
            if temporary_file is not None:
                try:
                    temporary_file.close()
                except BaseException:
                    pass
            self._remove_temporary_file(
                temporary_path
            )
            raise

        return output_file

    @staticmethod
    def _remove_temporary_file(
        temporary_path: Optional[Path],
    ) -> None:
        if temporary_path is None:
            return

        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass
