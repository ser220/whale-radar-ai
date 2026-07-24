# WR-101 — Backtest Pipeline Export Serialization Preflight Boundary

## Summary

The JSON file writer now completes serialization before performing
any filesystem mutation.

## Preflight behavior

`BacktestPipelineJSONFileWriter.write()` first obtains the complete
JSON string from its exporter. Only after successful serialization
does it create parent directories and write the destination file.

If serialization fails:

- the original exception propagates unchanged;
- no output directory or file is created;
- an existing destination file remains byte-for-byte unchanged.

## Compatibility

The writer's constructor, `write()` signature, return value, successful
export behavior, and public package API remain unchanged. Regular and
timestamped export-manager flows continue to use the shared writer.

This boundary does not add atomic writes, timestamp collision handling,
retention, persistence, a runner, or a CLI.
