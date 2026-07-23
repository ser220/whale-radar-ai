from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from app.backtest.pipeline.json_file_writer import (
    BacktestPipelineJSONFileWriter,
)
from app.backtest.pipeline.models import (
    BacktestPipelineResult,
)


class BacktestPipelineTimestampedJSONWriter:
    """
    Writes a backtest pipeline result to a timestamped
    JSON file inside an output directory.
    """

    def __init__(
        self,
        file_writer: Optional[
            BacktestPipelineJSONFileWriter
        ] = None,
        now_provider: Optional[
            Callable[[], datetime]
        ] = None,
    ) -> None:
        self._file_writer = (
            file_writer
            if file_writer is not None
            else BacktestPipelineJSONFileWriter()
        )
        self._now_provider = (
            now_provider
            if now_provider is not None
            else self._utc_now
        )

    def write(
        self,
        result: BacktestPipelineResult,
        output_directory: Path,
    ) -> Path:
        timestamp = self._format_timestamp(
            self._now_provider()
        )

        output_file = output_directory / (
            f"{result.report.strategy_id}"
            f"-{timestamp}.json"
        )

        return self._file_writer.write(
            result=result,
            output_file=output_file,
        )

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _format_timestamp(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(
                tzinfo=timezone.utc,
            )
        else:
            value = value.astimezone(
                timezone.utc,
            )

        return value.strftime(
            "%Y%m%dT%H%M%SZ"
        )
