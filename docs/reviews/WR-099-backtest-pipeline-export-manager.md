# WR-099 — Backtest Pipeline Export Manager

## Summary

Implemented a unified export manager for backtest pipeline results.

The export manager:

- provides a single entry point for pipeline exports;
- supports regular JSON export;
- supports timestamped JSON export;
- delegates file writing to existing pipeline components;
- keeps export logic separated from serialization and storage layers.

## Export flows

Supported:

```text
BacktestPipelineResult
        |
        v
BacktestPipelineExportManager
        |
        +--> BacktestPipelineJSONFileWriter
        |
        +--> BacktestPipelineTimestampedJSONWriter
