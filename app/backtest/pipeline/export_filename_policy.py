from pathlib import Path, PureWindowsPath


class BacktestPipelineExportFilenamePolicy:
    """
    Builds timestamped export filenames from safe strategy identifiers.
    """

    def build_filename(
        self,
        strategy_id: str,
        timestamp: str,
    ) -> str:
        self.validate_strategy_id(strategy_id)
        return f"{strategy_id}-{timestamp}.json"

    @staticmethod
    def validate_strategy_id(
        strategy_id: str,
    ) -> None:
        if not isinstance(strategy_id, str):
            raise ValueError(
                "strategy_id must be a string"
            )

        if not strategy_id.strip():
            raise ValueError(
                "strategy_id cannot be empty or whitespace"
            )

        if strategy_id in {".", ".."}:
            raise ValueError(
                "strategy_id must be a filename component"
            )

        if (
            Path(strategy_id).is_absolute()
            or PureWindowsPath(strategy_id).is_absolute()
        ):
            raise ValueError(
                "strategy_id cannot be an absolute path"
            )

        if "/" in strategy_id or "\\" in strategy_id:
            raise ValueError(
                "strategy_id cannot contain path separators"
            )

        if any(
            ord(character) < 32
            or ord(character) == 127
            for character in strategy_id
        ):
            raise ValueError(
                "strategy_id cannot contain ASCII control characters"
            )
