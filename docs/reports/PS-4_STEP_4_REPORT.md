# PS-4 Step 4 — Two-Scan Situation Evolution Report

## Objective

PS-4 Step 4 adds an isolated, process-local workflow that compares Timeline v1
objects from a second Early Bird scan with active timelines from a first scan.
It records whether each candidate creates a new situation or continues an
existing situation. It does not make trading decisions, persist state, learn,
or change any approved Early Bird, Emerging, Timeline, or Identity formula.

## Evolution workflow

1. The public Early Bird scanner produces the first ranked scan.
2. The approved Early Bird Timeline Adapter creates one Timeline v1 per
   successful ranked asset.
3. After a caller-controlled interval, the scanner produces a second scan.
4. The adapter creates independent candidate Timeline v1 objects for the
   second scan.
5. `SituationEvolutionEngine` normalizes deterministic asset order and compares
   each candidate with the active timeline for the same asset.
6. `SituationIdentityEngine` remains the sole continuity authority.
7. A matching candidate entry is explicitly copied with the existing timeline
   ID and appended through `append_timeline_entry()`.
8. A non-matching candidate remains a separate Timeline v1 and becomes the
   process-local active timeline for that asset.
9. Every successful action retains the full `SituationIdentityResult`; one
   asset failure is sanitized and isolated without aborting the batch.

## CREATED and CONTINUED semantics

- `CREATED` means no active timeline existed or Identity rejected continuity.
  The candidate remains version 1. When a prior timeline existed, its ID,
  version, and stage remain in decision provenance; the prior object is not
  mutated.
- `CONTINUED` means Identity matched. The existing timeline ID is preserved,
  its version increments exactly once, and the second candidate's sole entry is
  appended exactly once.

These actions are descriptive lifecycle records. They are not recommendations,
signals, direction, or execution authority.

## Append-only guarantees

- Existing and candidate timelines are immutable and never modified.
- Previous entries are reused unchanged and remain in their original order.
- Candidate DNA, timestamp, stage, source assessment/candidate IDs,
  expectations, observed facts, and transition reason are preserved.
- The copied continuation entry changes only `timeline_id` to the existing
  identity and adds the complete identity result to entry metadata.
- `append_timeline_entry()` enforces a new object and version increment.
- The engine never merges two existing timelines and never rewrites stage.

## Identity trace preservation

`SituationEvolutionDecision.identity_result` retains the approved Identity
contract without reduction. Its trace includes:

- hard-rejection flag and rejection code when present;
- all criterion scores and criterion weights;
- match threshold and maximum time gap;
- actual time gap when applicable;
- existing and candidate stages;
- Identity policy version;
- confidence and deterministic reason.

For assets without a prior timeline, the trace explicitly records that Identity
evaluation was not required. It does not imply a failed match.

## Situation DNA delta semantics

`extract_situation_dna_deltas()` compares the eight factor values plus
completeness, quality, freshness, Opportunity, Priority, Maturity, Emergence,
Horizon, and Detection Confidence in fixed order.

- measured → measured: records both values and their numeric delta;
- `None` → measured: `APPEARED`;
- measured → `None`: `BECAME_UNAVAILABLE`;
- `None` → `None`: no numeric material change;
- measured zero remains a measured value, never missing;
- factor availability changes are recorded separately from numeric changes;
- no directional or trading interpretation is added.

## Models and public API

- `EvolutionAction`: `CREATED`, `CONTINUED`
- `DeltaState`: `UNCHANGED`, `CHANGED`, `APPEARED`,
  `BECAME_UNAVAILABLE`
- immutable `SituationDNADelta`
- immutable `SituationEvolutionDecision`
- immutable `SituationEvolutionBatchResult`
- `SituationEvolutionEngine`
- `extract_situation_dna_deltas()`
- plain terminal formatters for one decision and a batch

All model timestamps are timezone-aware and normalized to UTC. Collections and
metadata are defensively frozen. Decision and batch models support lossless
`to_dict()` / `from_dict()` round trips.

## Two-scan manual verification

Command:

```bash
./venv/bin/python run_early_bird_evolution_demo.py \
  --limit 5 \
  --interval-seconds 60
```

Sanitized result captured on 2026-07-15:

- first scan: `2026-07-15T15:19:29.556043+00:00`;
- second scan: `2026-07-15T15:20:43.877529+00:00`;
- first-scan assets: XRP, ETH, LINK, PEPE, BTC;
- second-scan assets: XRP, ETH, LINK, PEPE, BTC;
- CREATED: 0;
- CONTINUED: 5;
- failed evolution: 0;
- every active timeline changed from version 1 to version 2;
- all stages remained `SEED`;
- identity confidence was 99.89 for all five assets.

The two scans used the same completed candle window. Factor values were stable;
the material deltas were time-derived freshness and related descriptive scores.
Examples:

- BTC freshness `92.5123 → 90.4478`, Horizon `90.0323 → 89.5162`;
- ETH Emergence `26.2285 → 25.9188`, Maturity `12.0784 → 12.2848`;
- LINK Priority `37.0580 → 36.5419`, Horizon `90.9764 → 90.4602`;
- PEPE Detection Confidence `69.2512 → 69.0448`;
- XRP Emergence `34.1856 → 33.8759`, Horizon `78.5841 → 78.0679`.

This output demonstrates continuity mechanics only. It makes no profitability
or prediction-accuracy claim.

## Files changed

- `app/intelligence/timeline/evolution.py` — models, deterministic deltas,
  evolution engine, and plain formatters.
- `app/intelligence/timeline/__init__.py` — public exports only.
- `run_early_bird_evolution_demo.py` — import-safe local two-scan orchestration.
- `test_situation_evolution.py` — focused offline tests.
- `docs/reports/PS-4_STEP_4_REPORT.md` — this report.

No approved runtime contract or formula file was modified.

## Verification

Compilation:

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/timeline/evolution.py \
  app/intelligence/timeline/__init__.py \
  run_early_bird_evolution_demo.py \
  test_situation_evolution.py
```

Focused result:

- `test_situation_evolution.py`: 28 passed.

Regression result:

- 450 unit tests passed, including the 28 new focused tests and all specified
  Identity, Timeline Adapter, Timeline, Emerging, Early Bird, MarketSituation,
  Fast, Correlation, Shadow, Contracts, and MarketState suites;
- `test_core.py`, `test_filter.py`, and `test_parser.py` passed.

Dependency audit confirms the evolution runtime imports only standard library,
Early Bird stage contracts, and local Timeline/Identity contracts. It does not
import Telegram, database, repositories, providers, exchanges, networking,
production pipeline, Decision Engine, Trade Readiness, MarketStateEngine, or
Experts. No third-party dependency was added.

## Production impact

- Production pipeline changed: **NO**
- Production decisions changed: **NO**
- Telegram changed: **NO**
- Hostinger changed: **NO**
- Deployment performed: **NO**
- Database or disk persistence added: **NO**
- Learning added: **NO**

## Open questions

1. Phase 1 keeps at most one active timeline per asset. A later design must
   define how multiple simultaneous situations for one asset are indexed and
   arbitrated.
2. Active timelines are process-local. Persistence, recovery, retention, and
   concurrency semantics require separate architecture approval.
3. The live demo uses the current scanner's completed-candle window, so scans
   one minute apart may differ mainly through freshness until a new candle
   closes.
4. A future stage may decide how inactive unmatched timelines are retained in a
   collection; Step 4 preserves their provenance in the decision but exposes
   only the current active mapping.
