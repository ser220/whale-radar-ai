# WR-026C Implementation Report

## Status

Implementation complete on `wr-026c-trend-observation-builder`; pending final
verification, commit, push, and Architecture Review.

## Summary

Added a pure deterministic trend observation builder between normalized candles
and WR-026A observation contracts. No production pipeline integration was made.

## Repository baseline

- Base: `origin/main` at `0810c341e63d64b17537313face75dd686571015`
- Tag: `v0.8-first-expert`
- Runtime: Python 3.9.6
- Existing foundations: WR-024.5, WR-025, WR-026A, WR-026B

## Files created

- `app/intelligence/builders/__init__.py`
- `app/intelligence/builders/candles.py`
- `app/intelligence/builders/trend/__init__.py`
- `app/intelligence/builders/trend/builder.py`
- `app/intelligence/builders/trend/policy.py`
- `app/intelligence/builders/trend/README.md`
- `test_trend_observation_builder.py`
- `docs/architecture/adr/ADR-WR-026C-trend-observation-builder.md`
- `docs/specs/WR-026C-trend-observation-builder.md`
- `docs/reports/WR-026C_REPORT.md`

## Files modified

None outside the files created for WR-026C.

## Public API

- `Candle`
- `TrendObservationBuilderPolicy`
- `TrendObservationBuilder`
- `TrendObservationBuilder.policy`
- `TrendObservationBuilder.build(...)`

## Candle validation

The frozen candle normalizes aware timestamps to UTC, requires finite positive
OHLC and finite non-negative volume, rejects booleans, enforces OHLC ordering,
and prevents close time from preceding open time. It round-trips through
primitive dictionaries.

## Formulas, thresholds, swing, BOS/CHOCH, and quality

The exact formulas and all defaults are recorded in
[`WR-026C-trend-observation-builder.md`](../specs/WR-026C-trend-observation-builder.md).
The architecture rationale and Phase 1 limitations are recorded in
[`ADR-WR-026C-trend-observation-builder.md`](../architecture/adr/ADR-WR-026C-trend-observation-builder.md).

Summary:

- latest-20 price change and long SMA, latest-5 short SMA;
- latest-10 normalized OLS slope;
- two adjacent 5-candle swing blocks;
- 0.10% relative swing/break tolerance and 0.05 flat threshold;
- five-point mirrored bias with a two-point lead;
- strength weights 30/25/20/25 with 5%/1%/2% normalizers;
- CHOCH precedence for opposing prior bias, then aligned BOS, then current
  evidence for neutral-prior BOS;
- transparent bounded count/regularity/volume/activity/coverage quality;
- real HTF bias intentionally unavailable.

## Observation ID format

`{ASSET}:{timeframe}:{observation_type}:v1:{latest_open_time_iso}`. An explicit
validated prefix may replace `{ASSET}:{timeframe}`. Identity is deterministic
and has no random or persistence dependency.

## Metadata behavior

Metadata includes counts, first/latest timestamps, median interval, irregular
ratio, SMAs, preceding reference range, policy version, and calculation window.
Structure metadata explicitly marks HTF bias unavailable. No raw candles are
stored, and serialized observations are JSON-compatible.

## Architecture deviations

None. The recommended layout and defaults are used. The specification permits a
generic iterable when safely materialized once; the implementation supports it.
At the minimum 20-candle input, the reference range necessarily uses the 19
preceding candles because the latest candle is excluded; this is explicitly
documented.

## Commands executed and test results

To be finalized after the complete verification pass.

## Dependency audit

Focused AST coverage rejects forbidden production builder imports. Final manual
audit pending.

## Production pipeline impact

None. Production webhook, filtering, scoring, clustering, Telegram, database,
API, services, and requirements files are not modified.

## Git information and full branch diff

To be finalized after commit and push.

## Breaking changes

None. The new package is additive and is not connected to current production
paths.

## Open questions

- Future empirical work may recalibrate strength normalizers.
- A future MTF builder must define genuine higher-timeframe bias.
- A later architecture task may decide whether weak/strong policy thresholds
  should produce a separate normalized categorical fact.

## Recommended next step

Architecture Review of WR-026C. Do not begin WR-026D before separate approval.
