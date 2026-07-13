# WR-025 — Market State Engine, Phase 1

## Status

Implementation and local verification complete on the dedicated feature
branch. Architecture Review is required before merge.

## Summary

Added a pure deterministic orchestration engine that consumes immutable
WR-024.5 `ExpertOpinion` values and synthesizes an explainable `MarketState`.
No Expert execution, production integration, infrastructure access, or WR-026
work is included.

## Architecture documents

- [ADR-WR-025](../architecture/adr/ADR-WR-025-market-state-engine.md)
- [WR-025 specification](../specs/WR-025-market-state-engine.md)

## Repository baseline

- Repository Python: 3.9.6
- Test framework: standard-library `unittest`; legacy safe smoke scripts
- Remote main baseline: `7b7cb57 v0.5 Whale Radar AI foundation`
- WR-024.5 reviewed base: `94d65b4 WR-024.5 add architecture records`
- WR-024.5 was not merged into `origin/main` when WR-025 started.
- Pre-existing untracked `docs/chat_archive/` is preserved and excluded.

## Branch base and ancestry

Branch `wr-025-market-state-engine` was created directly from reviewed
WR-024.5 commit `94d65b4`, avoiding duplication of the contracts. Its ancestry
is therefore `origin/main` → WR-024.5 feature commits → WR-025 commits.

## Files created

- `app/intelligence/market_state/__init__.py`
- `app/intelligence/market_state/engine.py`
- `app/intelligence/market_state/policy.py`
- `app/intelligence/market_state/README.md`
- `test_market_state_engine.py`
- `docs/architecture/adr/ADR-WR-025-market-state-engine.md`
- `docs/specs/WR-025-market-state-engine.md`
- `docs/reports/WR-025_REPORT.md`

## Files modified

- `app/intelligence/__init__.py` — convenience exports only.

No production file was modified.

## Public API

- `MarketStateEngine(policy: Optional[SynthesisPolicy] = None)`
- `MarketStateEngine.synthesize(opinions, *, weights=None, timestamp=None)`
- `MarketStateEngine.policy`
- Frozen `SynthesisPolicy`

Both classes are exported from `app.intelligence.market_state` and
`app.intelligence`.

## Exact formulas

For configured weight `c`, confidence `f`, and quality `q`:

```text
effective weight = c * (f / 100) * (q / 100)
quality weight = c * (q / 100)

direction balance = (bullish effective support - bearish effective support)
                    / total effective support
strength = effective-weighted mean(score)
overall confidence = quality-weighted mean(confidence)
continuation support = 100 * TREND effective support / total effective support
correction support = 100 * CORRECTION effective support / total effective support
reversal support = 100 * REVERSAL effective support / total effective support
market maturity proxy = effective-weighted mean(
    0.50 * score + 0.30 * confidence + 0.20 * quality
)
aggregate quality = configured-weighted mean(quality)

decision stability = 100 * min(contributor_count / 2, 1) * (
    0.30 * direction agreement
  + 0.25 * non-UNKNOWN state agreement
  + 0.25 * overall confidence / 100
  + 0.20 * aggregate quality / 100
)
```

All output metrics are clamped to `0..100` and rounded to six decimals.
Probability fields are independent support scores and need not sum to 100.

## Exact thresholds

- Direction: bullish at `>= +0.15`, bearish at `<= -0.15`, else neutral.
- Direction conflict: bullish and bearish support each `>= 20%`.
- State winner: support `>= 20%` and lead over runner-up `>= 10%`.
- Low aggregate quality warning: `< 50`.
- Insufficient contributors warning: fewer than two positive contributors.
- Explanation and warning caps: 20 each.

## Conflict handling

Material bullish/bearish support produces a direction-conflict warning. Split
meaningful state support without a winner produces `TrendState.UNKNOWN` and a
state-disagreement warning. These conditions do not raise exceptions.

## Empty-input handling

No opinions return `Direction.NEUTRAL`, `TrendState.UNKNOWN`, all zero numeric
metrics, and an explanatory warning. All-zero effective weight returns the same
safe zero state with no-positive-weight and insufficient-contributor warnings.

## Architecture deviations

None. The optional frozen policy object is allowed by the approved public API.
Unknown configured-weight names use the permitted ignore behavior and produce a
tested warning. The convenience export in `app/intelligence/__init__.py` is
additive and does not integrate the engine into production.

## Commands executed

```text
git status --short
git branch --show-current
git remote -v
git log -8 --oneline
git diff --stat origin/main...HEAD
./venv/bin/python --version
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile ...
./venv/bin/python -m unittest -v test_market_state_engine.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py
rg -n '^(from|import) ' app/intelligence/market_state app/intelligence/__init__.py
git diff --check
git diff --stat 94d65b4...HEAD
git diff --name-status 94d65b4...HEAD
git log --oneline 94d65b4..HEAD
git status --short
```

## Tests and results

- Python 3.9-compatible compile check: PASS
- WR-025 focused tests: 30/30 PASS
- WR-024.5 contract regression tests: 14/14 PASS
- Safe scorer smoke script (`test_core.py`): PASS
- Safe filtering smoke script (`test_filter.py`): PASS
- Safe Arkham payload parser smoke script (`test_parser.py`): PASS
- Live Telegram and network tests: intentionally excluded

## Dependency audit

The import audit shows that the market-state package imports only Python
standard-library modules, WR-024.5 contracts, and its local policy module. It
does not import Telegram, FastAPI, databases, repositories, persistence,
Arkham, funding, adapters, the pipeline, or networking. `requirements.txt` is
unchanged and no third-party dependency was added.

## Production pipeline impact

None. Arkham ingestion, filtering, scoring, clustering, database, Telegram,
and all existing production paths remain unchanged and do not import the new
engine.

## Git information

- Branch: `wr-025-market-state-engine`
- Implementation commit: `be5b3ea42264cd469bce7c0484e666e7d63e0063`
- Push: SUCCESS — `git push -u origin wr-025-market-state-engine`
- Remote branch: `origin/wr-025-market-state-engine`

## Branch diff and commit list

The complete implementation snapshot relative to reviewed WR-024.5 base
`94d65b4` is:

```text
app/intelligence/__init__.py                       |   3 +
app/intelligence/market_state/README.md            |  88 +++++
app/intelligence/market_state/__init__.py          |   6 +
app/intelligence/market_state/engine.py            | 422 +++++++++++++++++++++
app/intelligence/market_state/policy.py            |  60 +++
.../adr/ADR-WR-025-market-state-engine.md          | 129 +++++++
docs/reports/WR-025_REPORT.md                      | 197 ++++++++++
docs/specs/WR-025-market-state-engine.md           | 214 +++++++++++
test_market_state_engine.py                        | 317 ++++++++++++++++
9 files changed, 1436 insertions(+)
```

```text
M app/intelligence/__init__.py
A app/intelligence/market_state/README.md
A app/intelligence/market_state/__init__.py
A app/intelligence/market_state/engine.py
A app/intelligence/market_state/policy.py
A docs/architecture/adr/ADR-WR-025-market-state-engine.md
A docs/reports/WR-025_REPORT.md
A docs/specs/WR-025-market-state-engine.md
A test_market_state_engine.py
```

```text
be5b3ea WR-025 add market state engine
```

Status immediately after the implementation push:

```text
?? docs/chat_archive/
```

The remaining untracked archive is unrelated user data and is not staged or
committed. The report-only metadata commit that records the implementation hash
and push result does not change code, policy, tests, or architecture; its hash
is reported in the final completion response.

## Breaking changes

None.

## Open questions

No blocking questions. Phase 1 thresholds and the maturity proxy require later
domain calibration, but are explicit policy rather than hidden assumptions.

## Recommended next step

Architecture Review of the pushed WR-025 feature branch. Do not merge or begin
WR-026 without separate approval.
