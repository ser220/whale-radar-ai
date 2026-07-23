# WR-095 Backtest Pipeline Serializer

## Summary

Implemented a serializer for completed backtest pipeline results.

The serializer converts:

- final backtest report
- AI summary
- AI review

into a single JSON-compatible dictionary.

## Added

- `app/backtest/pipeline/serializer.py`
- `tests/backtest/pipeline/test_backtest_pipeline_serializer.py`
- `tests/backtest/pipeline/test_backtest_pipeline_serializer_flow.py`

## Updated

- `app/backtest/pipeline/__init__.py`

## Behaviour

`BacktestPipelineSerializer.serialize()` returns three sections:

- `report`
- `summary`
- `review`

Tuple-based review fields are converted to lists to ensure JSON compatibility.

## Verification

```bash
PYTHONPATH=. python -m py_compile \
app/backtest/pipeline/serializer.py
