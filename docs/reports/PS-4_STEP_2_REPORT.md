# PS-4 Step 2 Implementation Report

## Objective

Connect successful ranked Early Bird scan items to immutable, process-local
Market Situation Timeline version 1 records without persistence, production
integration, scoring changes, or stage inference.

## Base and branch

- Base: `origin/main` at `a5352d0`
- Branch: `ps-4-real-scan-to-timeline`
- Python: 3.9.6

## Files changed

- Created `app/intelligence/timeline/early_bird_adapter.py`.
- Updated `app/intelligence/timeline/__init__.py` with the Step 2 public API.
- Created `test_early_bird_timeline_adapter.py`.
- Created import-safe `run_early_bird_timeline_demo.py`.
- Created this report.

Approved Timeline models, Emerging Situation formulas, Early Bird scoring and
stage policy, scanner, Telegram, and production code were not modified.

## Adapter boundary

`EarlyBirdTimelineAdapter.create_timeline()` consumes a scan item plus its
already-created `EarlyBirdExplanation` and `EmergingSituation`. It validates
asset, assessment, and candidate identities, then creates exactly one
`MarketSituationTimelineEntry` inside a `MarketSituationTimeline` version 1.
The current stage is copied directly from `EmergingSituation.stage`; no stage
policy or transition logic exists in the adapter.

The adapter does not import the scanner module because that module owns the
existing provider execution boundary. It consumes the public scan-item shape
structurally. Only the local demo imports and invokes the scanner.

## Exact SituationDNA mapping

Authoritative factor data comes from `scan_item.build_result.factor_values`:

| Factor value | DNA value | Availability |
| --- | --- | --- |
| `AVAILABLE` | exact measured score, including `0.0` | exact status string |
| `MISSING` | `None` | `MISSING` |
| `STALE` | `None` | `STALE` |
| `UNSUPPORTED` | `None` | `UNSUPPORTED` |
| `ERROR` | `None` | `ERROR` |

The mapping covers whale activity, funding divergence, volume expansion,
structure event, momentum shift, relative strength, open-interest change, and
liquidity event.

- Completeness, quality, and freshness come from the built candidate.
- Opportunity, priority, and maturity come from the ranked assessment.
- Emergence, horizon, and detection confidence come from Emerging Situation.
- Metadata preserves source, timeframe, assessment/candidate IDs, source event
  and observation IDs, and already-present builder/policy/explanation/emerging
  versions. It does not copy raw provider payloads.

Funding remains `MISSING` on current main. The mapping is availability-driven,
so a future reviewed `AVAILABLE` funding value will be copied automatically
without funding-specific adapter code.

## TimelineEntry construction

- Stage is copied exactly from Emerging Situation.
- Supporting and limiting factors are copied from Emerging Situation.
- Expected, missing expected, and unexpected events are empty in Step 2.
- Observed events contain only namespaced stable source references and canonical
  measured-factor references.
- Unavailable factors never become missing expected events.
- Transition reason is deterministic:
  `Initial Early Bird assessment classified the situation as <STAGE>.`
- Source assessment and candidate IDs are preserved; source situation ID is
  `None`.

## Identity policy limitations

The adapter requires caller-supplied timeline and entry IDs and defines no
permanent global identity policy. The demo helper creates deterministic
run-local IDs from sanitized asset, scan timestamp, and candidate ID. These IDs
are explicitly not production identities and are not persisted.

## Batch behavior

`build_timelines_from_scan()` processes ranked items in order, creates the
explanation and Emerging Situation using the existing engines, and collects
successful Timeline results. An exception for one asset is captured as an
explicit construction error and does not abort other assets. Results also
contain deterministic top-asset order and stage distribution.

## Live sanitized verification

Command:

```bash
./venv/bin/python run_early_bird_timeline_demo.py --limit 5
```

Result at `2026-07-15T13:23:38.011761+00:00`:

- Successful scan assets: BTC, ETH, BNB, SOL, XRP, DOGE, SUI, LINK, NEAR, PEPE
- Failed scan assets: none
- Timelines created: 5
- Timeline construction failures: none
- Top five: ETH, SOL, NEAR, PEPE, XRP
- Stage distribution: `BUILDING=4`, `EMERGING=1`

| Asset | Opportunity | Emergence | Horizon | Detection confidence | Stage |
| --- | ---: | ---: | ---: | ---: | --- |
| ETH | 26.12 | 66.90 | 50.59 | 78.56 | BUILDING |
| SOL | 23.39 | 63.52 | 53.42 | 78.56 | BUILDING |
| NEAR | 23.94 | 52.63 | 72.90 | 75.23 | EMERGING |
| PEPE | 24.53 | 61.94 | 59.16 | 78.56 | BUILDING |
| XRP | 22.48 | 61.36 | 58.17 | 78.56 | BUILDING |

Availability was consistent across these five results: whale activity and
funding divergence were `MISSING`; open-interest change and liquidity event
were `UNSUPPORTED`; candle-derived volume, structure, momentum, and relative
strength were `AVAILABLE`. This is descriptive runtime output and makes no
claim about predictive value or profitability.

## Verification

- Python 3.9 compile: PASS.
- Adapter focused tests: 25 passed.
- Timeline and all requested Early Bird/Market Situation/intelligence
  regressions: 373 passed (398 unittest checks total).
- Safe smoke scripts: 3 passed.
- Dependency-boundary audits: PASS.
- Live public read-only demo: PASS.
- `git diff --check` and complete branch scope review are run before commit.

## Production impact

- Production pipeline changed: NO
- Production decisions changed: NO
- Telegram changed: NO
- Hostinger changed: NO
- Persistence/database/disk writes added: NO
- Deployment performed: NO
- Third-party dependency added: NO

## Open questions

- What permanent Timeline identity policy should production eventually use?
- Which reviewed expectation producer will first populate expected events?
- Should future persistence store every immutable Timeline version or entries
  plus reconstructable version metadata?
- When the separate funding work is reviewed and merged, which freshness policy
  will determine `AVAILABLE` versus `STALE` before this adapter boundary?
