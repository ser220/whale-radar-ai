# WR-098 — Backtest Pipeline Timestamped JSON Writer

## Summary

Implemented a timestamped JSON writer for backtest pipeline results.

The writer:

- accepts a `BacktestPipelineResult`;
- creates a UTC timestamp for the output filename;
- converts timezone-aware values to UTC;
- treats naive datetime values as UTC;
- delegates file creation to `BacktestPipelineJSONFileWriter`;
- returns the written `Path`.

## Filename format

```text
<strategy_id>-YYYYMMDDTHHMMSSZ.json
