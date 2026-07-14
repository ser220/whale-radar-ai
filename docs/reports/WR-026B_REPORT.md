# WR-026B — Trend Expert

## Status

Implementation and local verification complete on the dedicated feature
branch. Architecture Review is required before merge.

## Summary

Added the first independent Whale Radar AI Expert. `TrendExpert` consumes only
version 1 normalized trend/structure observations and returns one immutable,
explainable `ExpertOpinion`. No Builder, production integration, infrastructure,
trading decision, or WR-026C work is included.

## Architecture documents

- [ADR-WR-026B](../architecture/adr/ADR-WR-026B-trend-expert.md)
- [WR-026B specification](../specs/WR-026B-trend-expert.md)

## Repository baseline

- Base: `origin/main` at `6a3664f`
- Version: `v0.7-observation-foundation`
- Python: 3.9.6
- WR-024.5 contracts, WR-025 MarketStateEngine, and WR-026A observations present
- Test framework: standard-library `unittest` plus safe smoke scripts
- Pre-existing `docs/chat_archive/` remains untracked and excluded

## Files created

- `app/intelligence/experts/__init__.py`
- `app/intelligence/experts/trend/__init__.py`
- `app/intelligence/experts/trend/expert.py`
- `app/intelligence/experts/trend/policy.py`
- `app/intelligence/experts/trend/README.md`
- `test_trend_expert.py`
- `docs/architecture/adr/ADR-WR-026B-trend-expert.md`
- `docs/specs/WR-026B-trend-expert.md`
- `docs/reports/WR-026B_REPORT.md`

## Files modified

None. No broad `app.intelligence` re-export or production file is changed.

## Public API

- `TrendExpert(policy: Optional[TrendExpertPolicy] = None)`
- `TrendExpert.evaluate(trend, structure, *, timestamp=None) -> ExpertOpinion`
- `TrendExpert.name == "trend"`
- `TrendExpert.policy`
- Frozen `TrendExpertPolicy`

Exports are limited to `app.intelligence.experts.trend` and the focused
`app.intelligence.experts` namespace.

## Exact direction formula

Each side receives bias 25, MA alignment 15, two structure flags 12 each,
slope up to 10, price change up to 8, BOS 20 or CHOCH 12, and HTF bias 15.
Raw maximum is 117 and normalized support is `100 * raw / 117`. Bullish is a
signed lead at least +15, bearish at most -15, otherwise neutral.

## Exact state-classification rules

Precedence: low-quality UNKNOWN; supported opposing-CHOCH REVERSAL; at least two
short-term signals opposing directional HTF bias without opposing BOS
CORRECTION; aligned bias/MA/HTF plus same-side BOS or consistent swing flags
TREND; balanced weak in/near-range evidence without break RANGE; otherwise
UNKNOWN. CHOCH alone never forces REVERSAL.

## Exact score formula

`0.45 * evidence_strength + 0.30 * trend_strength + 0.25 * structure_support`,
bounded to 0..100. Neutral evidence strength measures balance classification,
not directional force.

## Exact confidence formula

`0.35 * agreement + 0.30 * confidence_quality + 0.25 * structure_clarity +
0.10 * timestamp_coherence`, with documented contradiction/BOS penalties,
low-quality cap, and Phase 1 reversal cap of 70. Structure clarity combines 70%
selected structural evidence with 30% builder-provided `structure_quality`
before penalties.

## Exact quality formula

`0.60 * TrendObservation.quality + 0.40 * StructureObservation.quality`.
Confidence additionally incorporates the lower of the two input qualities.

## Policy defaults

Direction lead 15, low quality 50, timestamp tolerance 300 seconds, reason and
warning limits 12, versions `(1,)`, policy version `"1.0"`, reversal support 25,
reversal confidence cap 70, weak slope 0.10, weak price change 1.0, insufficient
structure 25, and quality-gap warning 25.

## Supported versions

Only `TrendObservation.version == 1` and `StructureObservation.version == 1`.
Unsupported versions raise explicit `ValueError`; no migration exists.

## Explainability behavior

Reasons and warnings are concise, deterministic, deduplicated, and capped.
Metadata stores supports, signed lead, structure support, timestamp delta,
observation IDs, versions, timeframe, policy version, and classification flags.
It stores no observations or raw payloads.

## Architecture deviations

None. A focused `app.intelligence.experts` re-export is additive and allowed;
the broad `app.intelligence` API remains unchanged. Phase 1 reversal confidence
is always capped because one StructureObservation cannot simultaneously express
CHOCH and later BOS; this limitation is explicit in ADR/SPEC/README.

## Commands executed

```text
git status --short
git branch --show-current
git remote -v
git fetch origin
git rev-parse origin/main
git log -10 --oneline
git describe --tags --always
./venv/bin/python --version
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile ...
./venv/bin/python -m unittest -v test_trend_expert.py
./venv/bin/python -m unittest -v test_observation_contracts.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python -m unittest -v test_market_state_engine.py
./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py
rg -n '^(from|import) ' app/intelligence/experts
git diff --check
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
git log --oneline origin/main..HEAD
git status --short
```

## Test results

- Python 3.9 compile check: PASS
- Trend Expert tests: 42/42 PASS
- Observation regression tests: 46/46 PASS
- Intelligence contract regression tests: 14/14 PASS
- Market State regression tests: 30/30 PASS
- Safe scorer smoke script: PASS
- Safe filter smoke script: PASS
- Safe parser smoke script: PASS
- Live Telegram/network tests: intentionally excluded

## Dependency audit

Trend Expert production modules import only standard library, WR-024.5
contracts, WR-026A observations, and local Expert modules. No third-party
dependency is added.

## Production pipeline impact

None. Pipeline, Telegram, database/storage, API, source, service, and existing
MarketStateEngine implementation files are unchanged and do not invoke the
Expert.

## Git information

- Branch: `wr-026b-trend-expert`
- Implementation commit: recorded after successful verification
- Push: recorded after feature-branch push

## Full branch diff

Recorded after the verified implementation commit.

## Breaking changes

None.

## Open questions

No blocking questions. Coefficient calibration, deterministic builder formulas
for trend strength, MTF semantics, simultaneous CHOCH/BOS history, orchestration,
and additional Experts remain deferred.

## Recommended next step

Architecture Review of the pushed WR-026B feature branch. Do not merge or begin
WR-026C without explicit approval.
