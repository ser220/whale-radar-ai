# WR-097 — Backtest Pipeline JSON File Writer

## Summary

Implemented a file writer for backtest pipeline JSON exports.

The writer:

- accepts a `BacktestPipelineResult`;
- serializes it through `BacktestPipelineJSONExporter`;
- creates missing parent directories;
- writes UTF-8 JSON output to disk;
- returns the written `Path`.

## Files changed

- `app/backtest/pipeline/json_file_writer.py`
- `app/backtest/pipeline/__init__.py`
- `tests/backtest/pipeline/test_backtest_pipeline_json_file_writer.py`
- `docs/reviews/WR-097-backtest-pipeline-json-file-writer.md`

## Verification

Targeted tests:

```text
2 passed
