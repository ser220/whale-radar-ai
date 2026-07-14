# WR-027E — Hostinger Production Baseline

## Status

Baseline capture created for Architecture Review. This is an audit record, not
a deployment artifact. No Hostinger, service, database, environment, runtime
code, dependency, or secret was changed.

The record deliberately separates three evidence levels:

- **CONFIRMED BY OWNER** — production facts supplied for this task;
- **VERIFIED IN GIT OBJECT** — facts read from commit `d2182d2` in the local
  repository object database;
- **NOT VERIFIED ON HOST** — facts that require authenticated read-only access
  to the live VPS.

Read-only SSH access was attempted using the previously known VPS host and was
rejected because this audit environment has no accepted authentication. The
Hostinger control panel had no authenticated browser session. No password,
token, `.env` value, database content, or private key was requested or read.
Consequently this is a permanent **partial baseline** and must not be described
as full repository/deployment parity.

## Baseline identity

| Item | Baseline value | Evidence |
| --- | --- | --- |
| Baseline name | `production-v20` | Classification defined by WR-027E |
| Host role | Hostinger production, live Telegram bot | CONFIRMED BY OWNER |
| Repository path | `~/whale_radar_ai` | CONFIRMED BY OWNER |
| Production commit | `d2182d247ec72219bc2a12969e5d81542d9d569f` | Short hash CONFIRMED BY OWNER; full object VERIFIED IN GIT |
| Commit subject | `v20.4 track changes between live analyses` | VERIFIED IN GIT OBJECT |
| Commit date | `2026-07-12T06:10:28Z` | VERIFIED IN GIT OBJECT |
| Telegram bot | LIVE | CONFIRMED BY OWNER |
| Production branch | Unknown | NOT VERIFIED ON HOST |
| Dirty/untracked host files | Unknown | NOT VERIFIED ON HOST |
| Deployed remote | Unknown | NOT VERIFIED ON HOST |

`production-v20` is a baseline classification in this report. This task does
not create or move a `production-v20` Git branch or tag. A protected archival
branch/tag may be created only after a read-only host manifest proves that
commit `d2182d2` and its tracked tree fully represent the working runtime.

## Repository identity

### Commit and history

The exact Git object exists locally and has parent
`8359e60f606bb330b39a704d97fd885037d39aeb`.

```text
d2182d2 v20.4 track changes between live analyses
8359e60 v20.2 integrate live analysis with trade readiness
a043c5d v20.1 add trade readiness engine
b5a1adf v20.1 add canonical trade decision model
f961083 v19.1 build automatic evidence relationships
0ae79fe v19.1 map market facts to evidence nodes
a4cc5ef v19.1 add evidence graph foundation
66b1a4e v16-PERP-1 add unified open interest hub
d48ba98 v15-PERP-7 add unified funding Telegram command
9d35504 v15-PERP-6 add Bybit funding hot backup
```

### Tags

No local tag points exactly at `d2182d2`. Current descendant tags that contain
the commit are:

- `v0.6-intelligence-foundation`;
- `v0.7-observation-foundation`;
- `v0.8-first-expert`.

Those tags identify later repository states and must not be used as aliases for
the v20 production baseline.

### Remote

The audited local repository uses the `origin` remote at the private Whale
Radar AI GitHub repository. Whether the Hostinger checkout has the same remote
URL and fetch state is **NOT VERIFIED ON HOST**. The remote URL is intentionally
not duplicated here because operational identity should be recorded by remote
name and verified commit, not treated as a credential or deployment proof.

### Critical parity limitation

At `d2182d2`, tracked code imports but does not contain:

- `app/decision/decision_engine.py`;
- `app/decision/facts.py`;
- `app/intelligence/snapshot_builder.py`;
- `app/intelligence/market_snapshot.py`.

These missing modules are required by the intended `/analyze` chain. Since the
Telegram bot is confirmed live, the host may contain untracked/runtime files,
may run a process loaded before the reported checkout state, or may not exercise
that command path. None of those possibilities is assumed. A host file manifest
and service process inspection remain mandatory before migration or deployment.

## Runtime environment

| Item | Baseline value | Evidence |
| --- | --- | --- |
| Python version | Unknown | NOT VERIFIED ON HOST |
| Python executable | Unknown | NOT VERIFIED ON HOST |
| Virtual environment path | Unknown | NOT VERIFIED ON HOST |
| Operating system/distribution | Unknown | NOT VERIFIED ON HOST |
| Kernel/architecture | Unknown | NOT VERIFIED ON HOST |
| Installed dependency snapshot | Unknown | NOT VERIFIED ON HOST |
| Working directory | `~/whale_radar_ai` | CONFIRMED BY OWNER |

The repository contains Python 3.10-only union syntax in the production baseline
(`str | None`), so a previously reported local Python 3.9 engineering version
cannot be projected onto Hostinger. The actual production interpreter is a
blocking baseline field.

### Declared dependency names at `d2182d2`

This is the committed requirements declaration, **not** proof of installed
versions or transitive runtime state. Names only:

```text
annotated-doc
annotated-types
anyio
APScheduler
certifi
charset-normalizer
click
exceptiongroup
fastapi
h11
httpcore
httpx
idna
orjson
pydantic
pydantic_core
python-dotenv
python-telegram-bot
requests
starlette
typing-inspection
typing_extensions
tzlocal
urllib3
uvicorn
```

Future full capture should record names and versions from the active production
interpreter into a protected audit artifact. It must not install, upgrade, or
resolve packages during collection.

## Application structure at `d2182d2`

The following inventory is verified from the Git tree. Production importance
describes potential blast radius and known call paths; it does not prove that
each optional command is exercised on the host.

| Area / major component | Purpose | Production importance | Principal dependencies |
| --- | --- | --- | --- |
| `app/decision/trade_decision.py` | Canonical legacy trade/readiness result for UI clients | High for intended `/analyze` output | Python dataclasses |
| `app/decision/trade_readiness_engine.py` | Applies confidence, quality, stability and confirmation caps; emits NO_TRADE/WATCH/PREPARE/READY/ACTION | High for `/analyze`; upstream import path incomplete in Git | `TradeDecision`, Decision v2 dictionary, snapshot quality |
| `app/decision/evidence/` | Maps facts to evidence nodes and pairwise support/contradiction graph | High for intended explanation path; import incomplete | Missing `MarketFact`, evidence dataclasses |
| `app/intelligence/snapshot_fact_builder.py` | Intended conversion of Arkham/funding/OI/price snapshot blocks into facts | High for `/analyze`; cannot import from Git tree alone | Missing `MarketSnapshot` and `MarketFact` |
| `app/services/analyze_service.py` | Intended Arkham + live market → facts → evidence → decision → readiness orchestration and change tracking | High Telegram command capability; import incomplete | Missing snapshot/decision modules, SQLite state repository |
| Funding snapshot services | Read-only OKX, Binance, Gate and Bybit funding/history/mark/index/basis loaders | Medium; `/funding` command and intended snapshot input | Public exchange REST, standard-library HTTP/JSON |
| `app/services/unified_funding_hub.py` | Concurrent funding aggregation, execution-set selection and consensus | Medium; live read-only command | Four funding services, exchange registry |
| `app/services/unified_open_interest_hub.py` | Concurrent cross-exchange OI snapshot/concentration | Medium; intended analysis input | OKX/Binance/Gate/Bybit public REST |
| Lifecycle/review services | Build candle-backed prediction lifecycle, outcome review and learning recommendations | Medium; Telegram review/shadow behavior | Prediction repositories, Binance candle source, SQLite |
| `app/repository/analysis_state_repository.py` | Stores latest per-asset analysis state for changes between analyses | High for v20.4 intended behavior | SQLite and configured DB path |
| Prediction/context/recommendation repositories | Persist prediction history, context and shadow recommendations | Medium–high for lifecycle/learning | SQLite, domain models |
| `app/engine/pipeline.py` | Critical webhook flow: filter, store, score, cluster, intelligence, alert gate, prediction save, Telegram send | **Critical** | sources, SQLite storage, engine modules, Telegram sender |
| `app/engine/intelligence.py` | Monolithic legacy market/wallet/regime/probability/risk/scenario/meta orchestration | **Critical** for webhook alerts | Many engine modules, SQLite history, Binance spot |
| Filter/scorer/context/alert engines | Noise and size gates, direction score, in-memory clusters, alert eligibility | **Critical** | `MarketEvent`, static policy, SQLite/in-memory state |
| Wallet/campaign/history engines | Derive wallet profiles, memory, behavior and campaign context | High through legacy intelligence | SQLite events, heuristic policies |
| Probability/risk/scenario/decision/plan engines | Produce legacy decision, targets, risk and user guidance | **Critical** alert content | Computed legacy evidence, Binance spot price |
| Outcome/learning engines | Persist and evaluate predictions and update shadow learning | High for persistence; medium for commands | SQLite, live price, domain services |
| `app/telegram/polling_bot.py` | Registers Telegram commands and starts polling | **Critical** live bot entry point | `python-telegram-bot`, services, engines, repositories |
| Telegram formatters | Render compact alert, detailed signal and `/analyze` UI | **Critical** presentation | Event/intelligence dictionaries |
| `app/telegram/sender.py` | Sends outbound Bot API alerts | **Critical** webhook delivery | `requests`, runtime environment variables |

### Git-tree module counts

```text
app/decision/      8 tracked Python files
app/intelligence/  1 tracked Python file
app/services/     18 tracked Python files
app/repository/    5 tracked Python files
app/engine/       79 tracked Python files
app/telegram/      7 tracked Python files
```

These counts identify the `d2182d2` tree, not host-only files. The later
Observation/Expert/MarketState packages are not part of this production commit.

## Telegram runtime baseline

| Item | Baseline value | Evidence |
| --- | --- | --- |
| Bot health | LIVE | CONFIRMED BY OWNER |
| Process/service name | Unknown | NOT VERIFIED ON HOST |
| Actual start command | Unknown | NOT VERIFIED ON HOST |
| Source-supported polling entry point | `app.telegram.polling_bot` module calling `run_bot()` | VERIFIED IN GIT OBJECT |
| Working directory | `~/whale_radar_ai` | CONFIRMED BY OWNER |
| Execution user | Unknown | NOT VERIFIED ON HOST |
| PID/start time | Unknown | NOT VERIFIED ON HOST |
| Service manager/restart policy | Unknown | NOT VERIFIED ON HOST |
| Logging destination/rotation | Unknown | NOT VERIFIED ON HOST |

The source-supported command must not be documented as the actual production
start command until the process/service definition is read on Hostinger. No
service status or journal command was executed because authentication failed.

## Database baseline

| Item | Baseline value | Evidence |
| --- | --- | --- |
| Database type | SQLite | VERIFIED IN GIT OBJECT |
| Configured relative location | `data/whale_radar.db` under application base | VERIFIED IN GIT OBJECT |
| Expected host location | `~/whale_radar_ai/data/whale_radar.db` | Derived from confirmed path + Git config; NOT VERIFIED ON HOST |
| Actual location/symlink | Unknown | NOT VERIFIED ON HOST |
| File size | Unknown | NOT VERIFIED ON HOST |
| Journal/WAL mode | Unknown | NOT VERIFIED ON HOST |
| Schema/version | Partly created lazily by code; live schema unknown | Git behavior verified; host schema NOT VERIFIED |
| Last backup/integrity result | Unknown | NOT VERIFIED ON HOST |

No database connection, read, lock, checkpoint, copy, backup, integrity check,
or schema operation was performed.

### Backup considerations

- Capture actual path, size, journal mode and active writers before choosing a
  backup method.
- Use SQLite-aware online backup or an approved write quiescence window; do not
  assume a raw file copy is consistent during WAL/write activity.
- Record checksum, schema version, release commit, capture time and retention.
- Test restore away from production before the backup becomes a rollback
  dependency.
- Keep database/backups outside Git and outside replaceable release directories.

## Environment variable-name baseline

Only names referenced by the baseline source are documented. No value was read
or reproduced.

| Variable/configuration name | Status |
| --- | --- |
| `BOT_TOKEN` | Required by polling startup; configuration is functionally implied by owner-confirmed LIVE bot, but NOT directly inspected |
| `CHAT_ID` | Required by webhook alert sender; NOT directly inspected |
| Webhook secret configuration | Present as a source-level constant at `d2182d2`, not an environment variable; value intentionally omitted and should be externalized/rotated in a separate reviewed security task |

No other environment variable is referenced through `os.getenv`/`os.environ`
in the tracked application tree at `d2182d2`. That statement does not exclude
host service variables, wrapper scripts, shell configuration, or untracked
files, all of which remain unverified.

## `production-v20` baseline classification

Purpose:

1. **Rollback reference** — exact last-known working release to restore when a
   later deployment fails, after database compatibility is assessed.
2. **Migration comparison** — stable semantic baseline for alert volume,
   direction, confidence, readiness, latency and Telegram output.
3. **Shadow-testing reference** — legacy output remains authoritative while new
   Observations, Experts and MarketState run without production influence.

Acceptance requirements before materializing the baseline branch/tag:

- authenticated read-only host Git status, branch, commit, remote and manifest;
- Python executable/version and installed dependency snapshot;
- service/process entry point, user, working directory and logging;
- database path/size/journal/schema/backup state;
- environment variable names only and configuration ownership;
- reconciliation of host-only files and the four missing Git modules;
- confirmation that capturing the baseline exposes no secret or runtime data.

Until those checks pass, `d2182d2` is the **owner-confirmed working commit**, not
a proven complete deployment artifact.

## Migration role

```text
Arkham webhook/adapter
  -> Provider Source Adapter
  -> normalized transfer record
  -> OnChainObservation

Funding adapters/hub
  -> derivatives source records
  -> DerivativesObservation

Open Interest hub
  -> derivatives source records with time-aligned delta
  -> DerivativesObservation

Evidence facts/graph
  -> normalized Observations
  -> Expert-internal reasoning support

Legacy Decision + Trade Readiness
  -> MarketState-consuming Decision Layer
  -> readiness remains above intelligence

Prediction Lifecycle/Review
  -> Management Layer for post-decision tracking and evaluation
```

Legacy behavior remains active during hybrid shadow validation. Current OI
magnitude is not directional until a deterministic historical delta exists.
The Evidence Graph does not become a new market-data Observation; interpretive
relationships belong inside Expert reasoning or a non-signal explanation view.

## Full baseline capture commands for an authorized host session

The following categories remain to be collected read-only; this is a checklist,
not a deployment script and contains no credentials:

- Git: path, status, branch, commit, tags, remote and recent log;
- runtime: Python executable/version, active venv and installed package names;
- OS: release, kernel and architecture;
- structure: tracked manifest plus host-only/untracked application files;
- process: service manager definition/status, PID, user, command, cwd and logs;
- database: resolved path, metadata, size, journal/schema versions and backup
  inventory without opening or copying the live database;
- environment: names only from the service environment/configuration, with
  values redacted before output.

The exact commands require Architecture/Operations approval because even
read-only process and environment inspection may expose sensitive values if not
carefully filtered.

## Verification and impact

- Documentation file created: **YES**.
- Production Python changed: **NO**.
- Requirements changed: **NO**.
- Hostinger changed: **NO**.
- Service restarted: **NO**.
- Database read or changed: **NO**.
- Secret value read or exposed: **NO**.
- `.env` read or changed: **NO**.
- Deployment/migration script created: **NO**.
- Full runtime independently verified: **NO — access unavailable**.
- Owner-confirmed working baseline commit preserved in documentation: **YES**.

## Open items

1. Provide an approved read-only Hostinger session or sanitized command output
   for the unverified host fields.
2. Reconcile the live bot with the four missing tracked `/analyze` modules.
3. Confirm production Python compatibility and installed dependency versions.
4. Identify service manager, start command, user, logs and single-instance
   guarantees for Telegram polling.
5. Capture database metadata and verified backup/restore posture.
6. Only then create the protected `production-v20` branch/tag and use it as a
   deployment rollback artifact.
