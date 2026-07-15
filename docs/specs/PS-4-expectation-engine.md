# PS-4 Step 5 — Market Situation Expectation Engine Specification

## Objective

Create deterministic, immutable hypotheses describing what measurable event is
expected next from the latest state of a Market Situation Timeline.

## Scope

- pure expectation model and enums;
- frozen Phase 1 policy;
- deterministic rule engine;
- source value and availability snapshot;
- deterministic IDs and ordering;
- fulfillment and contradiction criteria;
- plain terminal formatting;
- one-scan local demonstration;
- standard-library tests and documentation.

## Out of scope

- expectation evaluation or status;
- observed outcomes;
- learning or historical similarity;
- probabilities of profit;
- trade direction or execution advice;
- provider or scanner calls from runtime;
- persistence, cache, database, or disk writes;
- production, Telegram, or deployment integration.

## Public API

- `ExpectationKind`
- `ExpectationStrength`
- `ExpectationPolicy`
- immutable `SituationExpectation`
- `SituationExpectationEngine.generate()`
- `deterministic_expectation_id()`
- `format_situation_expectation()`
- `format_situation_expectations()`

## Model contract

`SituationExpectation` stores:

- expectation, timeline, source-entry, asset, and version identity;
- UTC creation and evaluation-window timestamps;
- kind, strength, subject, and description;
- non-empty basis, fulfillment criteria, and contradiction criteria;
- source stage;
- all eight source factor values and availability states;
- deeply frozen metadata containing policy version, rule name, source-entry
  timestamp, generation semantics, and evaluation contract version `"1"`.

It contains no evaluation status, observed outcome, market direction, trading
instruction, or execution field.

### Evaluation contract amendment

Every newly generated expectation stores `metadata.evaluation_contract` with
common fields `contract_version`, `rule_name`, `expectation_kind`, `subject`,
`source_policy_version`, `source_timeline_version`, `source_stage`, and
`window_minutes`. Rule-specific fields preserve only the thresholds,
availability states, factor names, stages, and evidence counts required by that
rule. The structure is deeply frozen and primitive/serializable only.

Historical payloads without this additive field continue to deserialize. The
contract format is version `"1"`; the existing expectation policy remains
version 1. Current defaults may never repair an absent historical contract.

## Validation

- required identifiers and descriptive text cannot be blank;
- asset is normalized uppercase;
- timeline version is an integer of at least 1;
- timestamps must be timezone-aware and normalize to UTC;
- `created_at <= window_start <= window_end`;
- basis, fulfillment criteria, and contradiction criteria are non-empty,
  ordered, and duplicate-free;
- all eight factor keys must be present in both source mappings;
- `AVAILABLE` requires a measured 0..100 value;
- non-`AVAILABLE` requires `None`;
- booleans are rejected as numeric values;
- metadata is deeply frozen and serializable;
- `to_dict()` and `from_dict()` preserve enums, timestamps, mappings, and
  measured zero.

## Policy defaults

- default window: 60 minutes;
- short window: 30 minutes;
- long window: 120 minutes;
- material factor: 25;
- strong factor: 60;
- weak confirmation: 35;
- high maturity: 70;
- low horizon: 30;
- minimum detection confidence: 40;
- maximum expectations: 5;
- policy version: 1.

## Rule conditions

### 1. Volume confirmation

Generate when measured Structure Event is at least material, measured Volume
Expansion is below weak confirmation, and Detection Confidence is sufficient.
Unavailable volume is not weak volume.

### 2. Momentum confirmation

Generate when measured Structure Event or Volume Expansion is material,
measured Momentum Shift is below weak confirmation, and Detection Confidence is
sufficient. Unavailable momentum is not weak momentum.

### 3. Factor persistence

Generate separately for measured Whale Activity, Funding Divergence, Structure
Event, or Volume Expansion at or above the strong threshold.

### 4. Factor appearance

Generate only for Funding Divergence when it is `MISSING`, both measured
Structure Event and Volume Expansion are strong, and Detection Confidence is
sufficient. No whale-appearance rule exists. `UNSUPPORTED` and `ERROR` do not
qualify.

### 5. Stage advance

Generate only for `SEED -> EMERGING` or `EMERGING -> BUILDING` when Emergence
and Horizon are strong, Detection Confidence is sufficient, and at least two
independent supporting factors are measured. No stage jump is allowed.

### 6. Stage persistence

Generate only for SEED, EMERGING, or BUILDING when no stage advance was
generated, maturity is below high, horizon is above low, Detection Confidence
is sufficient, and at least one supporting factor is measured.

### 7. Invalidation risk

Generate when maturity is high, horizon is low, measured support is concentrated
in one factor, or measured confirmation is weak behind material structure. It
describes classification-maintenance risk, not a directional action.

## Windows

- confirmation and stage persistence: default 60 minutes;
- factor persistence and invalidation risk: short 30 minutes;
- factor appearance and stage advance: long 120 minutes.

Window start equals creation time. No expectation is created after its window
end.

## Determinism and anti-hindsight

- default creation time is the exact Timeline `updated_at`;
- default ID derives from timeline ID, version, rule name, and subject;
- output order is policy rule order, then subject, then expectation ID;
- maximum expectations is applied only after sorting;
- generation uses only the latest Timeline entry;
- source values, availability, stage, entry ID, Timeline version, and policy
  version are copied and immutable;
- later facts and policy changes cannot modify prior expectations.
- stored evaluation contracts are authoritative for future evaluation;
- descriptive criteria remain presentation and are never parsed as rules;
- historical records without a contract remain valid but evaluate uncertainly.

## Dependency boundary

Runtime imports only standard library, Timeline models, and public
`EmergingStage`. The demo alone may call the existing public scanner and
Timeline adapter. No third-party dependency is added.

## Acceptance criteria

- all model and policy validations pass;
- all seven rules and negative availability cases pass;
- no evaluation or trade fields exist;
- identical input is deterministic;
- Timeline input remains unchanged;
- formatter says `NOT EVALUATED` without storing status;
- demo is import-safe and write-free;
- focused and regression tests pass;
- dependency and production-scope audits pass.

## Verification commands

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile \
  app/intelligence/timeline/expectations.py \
  app/intelligence/timeline/__init__.py \
  run_situation_expectation_demo.py \
  test_situation_expectations.py

./venv/bin/python -m unittest -v test_situation_expectations.py
./venv/bin/python -m unittest -v test_situation_evolution.py
./venv/bin/python -m unittest -v test_situation_identity.py
./venv/bin/python -m unittest -v test_early_bird_timeline_adapter.py
./venv/bin/python -m unittest -v test_market_timeline.py
./venv/bin/python -m unittest -v test_emerging_situation.py
./venv/bin/python -m unittest -v test_early_bird_explainability.py
./venv/bin/python -m unittest -v test_early_bird_candle_factors.py
./venv/bin/python -m unittest -v test_early_bird_scanner.py
./venv/bin/python -m unittest -v test_early_bird_candidate_builder.py
./venv/bin/python -m unittest -v test_early_bird_availability.py
./venv/bin/python -m unittest -v test_early_bird.py
./venv/bin/python -m unittest -v test_market_situation.py
./venv/bin/python -m unittest -v test_fast_intelligence.py
./venv/bin/python -m unittest -v test_intelligence_correlation.py
./venv/bin/python -m unittest -v test_shadow_intelligence.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python -m unittest -v test_market_state_engine.py

./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py

./venv/bin/python run_situation_expectation_demo.py --limit 5 --timeframe 15m
```
