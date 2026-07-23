# WR-096 Backtest Pipeline JSON Exporter

## Summary

Implemented a JSON export layer for completed backtest pipeline results.

The exporter converts the existing serializer output into a stable,
human-readable JSON string suitable for API responses, file persistence,
and downstream integrations.

## Changes

- Added `BacktestPipelineJSONExporter`
- Added JSON export from `BacktestPipelineResult`
- Added direct export from JSON-compatible dictionaries
- Added deterministic key ordering
- Added UTF-8-safe JSON output
- Added public package export
- Added focused unit tests

## Files

- `app/backtest/pipeline/json_exporter.py`
- `app/backtest/pipeline/__init__.py`
- `tests/backtest/pipeline/test_backtest_pipeline_json_exporter.py`
- `docs/reviews/WR-096-backtest-pipeline-json-exporter.md`

## Verification

```text
PYTHONPATH=. python -m py_compile \
app/backtest/pipeline/json_exporter.py \
tests/backtest/pipeline/test_backtest_pipeline_json_exporter.py
