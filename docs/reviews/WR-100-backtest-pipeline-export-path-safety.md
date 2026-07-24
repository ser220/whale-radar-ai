# WR-100 — Backtest Pipeline Export Path Safety Boundary

## Summary

Introduced a dedicated filename policy for timestamped backtest
pipeline exports.

The policy:

- treats `strategy_id` as one filename component;
- rejects empty and whitespace-only values;
- rejects `.` and `..`;
- rejects path separators and absolute paths;
- rejects NUL and all ASCII control characters;
- raises `ValueError` without sanitizing or rewriting input;
- preserves accepted `strategy_id` values unchanged.

## Filesystem boundary

`BacktestPipelineTimestampedJSONWriter` applies the injected policy
before delegating to the file writer. Because directory creation
remains inside that later delegate, a rejected identifier creates no
directory or file.

For accepted identifiers, the generated timestamped JSON path remains
a direct child of the caller-provided `output_directory`.

## Compatibility

The writer's existing public arguments and `write()` method are
unchanged. Filename policy injection is an optional constructor
argument. `BacktestPipelineExportManager` requires no changes and
continues to delegate timestamped exports through the writer.

The boundary uses only Python standard-library production
dependencies and Python 3.9-compatible `Optional` typing.
