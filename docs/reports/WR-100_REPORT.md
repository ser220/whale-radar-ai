# WR-100 Report — Backtest Pipeline Export Path Safety Boundary

## Scope

Added an isolated filename policy and injected it into the existing
timestamped JSON writer. No serialization, report, export-manager, or
storage APIs were redesigned.

## Implementation

- Added `BacktestPipelineExportFilenamePolicy`.
- Validated `strategy_id` before any directory or file creation.
- Preserved valid identifiers exactly.
- Kept valid timestamped exports as direct children of the requested
  output directory.
- Exported the policy through `app.backtest.pipeline`.

## Safety guarantees

Rejected values raise `ValueError` and are never sanitized. Rejection
covers empty or whitespace-only values, dot components, path
separators, absolute paths, NUL, and every ASCII control character.

## Verification

- Changed Python files compile successfully under Python 3.9.6.
- Focused WR-100 and export-manager tests: 55 passed.
- All `tests/backtest/pipeline` tests: 63 passed.
- Deterministic project regression excluding four pre-existing live
  Telegram scripts: 1383 passed, 1 environment warning.
- The unfiltered full regression was run and stopped during collection
  because four pre-existing root-level scripts perform live Telegram
  network calls. The restricted environment rejected those calls; no
  WR-100 test failed.
