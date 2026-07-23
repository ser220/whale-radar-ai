import json
from typing import Any, Dict

from app.backtest.pipeline.models import (
    BacktestPipelineResult,
)
from app.backtest.pipeline.serializer import (
    BacktestPipelineSerializer,
)


class BacktestPipelineJSONExporter:
    """
    Exports a completed backtest pipeline result
    as a stable JSON string.
    """

    def __init__(
        self,
        serializer: BacktestPipelineSerializer = None,
    ) -> None:
        self._serializer = (
            serializer
            if serializer is not None
            else BacktestPipelineSerializer()
        )

    def export(
        self,
        result: BacktestPipelineResult,
    ) -> str:
        data = self._serializer.serialize(result)

        return self.export_data(data)

    def export_data(
        self,
        data: Dict[str, Any],
    ) -> str:
        return json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
