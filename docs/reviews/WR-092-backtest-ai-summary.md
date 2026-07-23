# WR-092 — Backtest AI Summary

## Summary

Implemented a deterministic AI-style summary layer for completed backtest reports.

The new component converts backtest decision data into a concise human-readable interpretation containing:

- strategy identifier
- decision
- headline
- explanation
- risk level
- confidence

## Added

### Application

- `app/backtest/summary/__init__.py`
- `app/backtest/summary/models.py`
- `app/backtest/summary/generator.py`

### Tests

- `tests/backtest/summary/__init__.py`
- `tests/backtest/summary/test_backtest_ai_summary.py`
- `tests/backtest/summary/test_backtest_ai_summary_flow.py`

## Integrated

The summary layer is exported through:

- `app.backtest.summary`
- `app.backtest`

Pipeline:

```text
BacktestFinalReport
        ↓
AISummaryGenerator
        ↓
BacktestAISummary
