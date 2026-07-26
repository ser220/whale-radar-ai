# WR-027C Legacy to Intelligence Migration Map Report

## Status

Completed on feature branch `wr-027c-legacy-migration-map`; pending Architecture
Review. No merge or implementation is included.

## Objective

Map valuable production capabilities at Hostinger commit `d2182d2` into the new
Observation → Expert → MarketStateEngine architecture without interrupting the
live Telegram system or assuming that missing repository modules exist.

## Deliverables

- Architecture map:
  [`WR-027C_LEGACY_MIGRATION_MAP.md`](../architecture/WR-027C_LEGACY_MIGRATION_MAP.md)
- This implementation report.

## Scope inspected

- `app/decision/`
- `app/intelligence/`
- `app/services/`
- `app/repository/`
- `app/engine/`
- `app/telegram/`
- Arkham, funding, OI, evidence, readiness, lifecycle and Telegram flows.

The analysis reuses the evidence-based WR-027A capability audit and the local
WR-027B production inventory, while independently preserving the distinction
between tracked code, reported live behavior, and untracked WR-026C work.

## Major decisions

1. Production preservation and repository/deployment parity are Phase 0 and
   Phase 1; no provider or intelligence rollout precedes them.
2. Arkham becomes a provider-neutral OnChain Source Adapter feeding an
   OnChainFlow Observation Builder and Expert.
3. Funding and OI venue access remain useful source adapters. Aggregation and
   normalized facts move to a Derivatives Observation Builder; interpretation
   moves to a Derivatives Expert.
4. Current OI magnitude is not directional until deterministic OI deltas exist.
5. The universal Evidence Graph does not become an Observation. Evidence
   relations are Expert-internal; an optional Decision explanation graph may
   consume opinions without becoming another signal.
6. MarketStateEngine precedes the future Decision Engine. Trade Readiness sits
   above both and remains an operational gating policy.
7. Lifecycle remains post-decision management/evaluation. Telegram remains UI.
8. The monolithic legacy pipeline is migrated last and remains the production
   control throughout shadow comparison.

## Migration phases

1. Phase 0 — Production preservation.
2. Phase 1 — Repository parity and reproducibility.
3. Phase 2 — Source normalization.
4. Phase 3 — Observation migration.
5. Phase 4 — Expert migration.
6. Phase 5 — Shadow decision comparison.
7. Phase 6 — Production intelligence rollout.

Every phase defines its objective, components, risk, rollback, and explicit
advancement gate in the architecture map.

## Repository parity constraint

The tracked production tree imports but does not contain:

- `app/decision/decision_engine.py`;
- `app/decision/facts.py`;
- `app/intelligence/snapshot_builder.py`;
- `app/intelligence/market_snapshot.py`.

The live bot claim and the tracked tree therefore cannot yet be treated as
equivalent. The map does not reconstruct these modules or modify Hostinger.

## Architecture deviations

None from the task. The requested destination vocabulary is used. The Evidence
Graph question is resolved in favor of Expert-internal evidence support rather
than a new `EvidenceObservation`, because graph relationships are interpretation
rather than normalized facts.

## Files created

- `docs/architecture/WR-027C_LEGACY_MIGRATION_MAP.md`
- `docs/reports/WR-027C_REPORT.md`

## Files modified

None.

## Production impact

- Production Python changed: **NO**
- Requirements changed: **NO**
- Hostinger changed: **NO**
- Services restarted: **NO**
- Adapters/contracts implemented: **NO**
- Database touched: **NO**
- Telegram behavior changed: **NO**

## Preserved unrelated work

- `docs/chat_archive/` remains untracked and unstaged.
- Untracked WR-026C builder, test, ADR, specification and report remain
  untouched and unstaged.
- The untracked WR-027B inventory remains untouched and unstaged.

## Verification

Required before commit:

```bash
git status --short
git diff --check
git diff --name-status --cached
```

The staged scope must contain only the WR-027C architecture map and report. A
sanitized secret-pattern check must find no credential assignment or `.env`
content. Documentation-only work does not require production tests and must not
start services or make provider calls.

## Breaking changes

None. Documentation only.

## Open questions

The authoritative deployed `/analyze` files, Hostinger Python/dependencies,
process entry points, schema history, shadow parity thresholds, explanation
format, data retention, and rollout flag/rollback mechanism remain unresolved.
They must be answered in reviewed follow-up tasks; no implementation task starts
automatically.
