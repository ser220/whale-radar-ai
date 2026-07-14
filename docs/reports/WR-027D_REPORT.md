# WR-027D GitHub ↔ Hostinger Deployment Architecture Report

## Status

Completed on `wr-027d-deployment-architecture`; pending Architecture Review.
Documentation only. No production action is authorized by this report.

## Objective

Define a safe future synchronization and deployment model in which GitHub is
the source of application truth, Hostinger is deployment-only, the live v20 bot
continues operating during migration, and every release has database-aware
rollback and protected secret handling.

## Deliverables

- [Deployment architecture](../architecture/WR-027D_DEPLOYMENT_ARCHITECTURE.md)
- This report.

## Branch base

The feature branch was based directly on current `origin/main` at `fe921cd`.
It does not include the WR-027C feature-branch commit or history.

## Recommendation

Use a two-step maturity path:

1. **Immediate:** controlled manual deployment using an approved runbook,
   immutable release directories, a previous-release pointer, SQLite-aware
   backup, restricted SSH and explicit verification/rollback.
2. **Target:** GitHub Actions SSH deployment only after repository/Hostinger
   parity and at least one safe release/rollback rehearsal. Use protected tag
   deployment, a GitHub Environment approval and a restricted deploy account.

A self-hosted production deployment agent is not justified at current scale and
would add excessive host and maintenance risk.

## Architecture summary

```text
feature branch -> tests -> Architecture Review -> protected main
  -> release candidate -> immutable tag -> approved deployment
  -> Hostinger verification -> Telegram bot
```

`main` is reviewed/releasable, `feature/*` (including current `wr-*` branches)
is isolated development, `production-v20` is a protected verified legacy
baseline, and `release/*` is temporary candidate stabilization. Deployment is a
separate approval from merge.

## Hostinger target

- immutable release directories and atomic active-release pointer;
- release-specific reproducible Python environment;
- `.env`, SQLite, backups and logs outside Git checkouts;
- non-root deploy/service identities with least privilege;
- service-manager-controlled process lifecycle;
- no manual Python edits, server commits or in-place `git pull` deployment.

## Database and rollback decisions

- Use SQLite-aware consistent backups and validate restore before schema work.
- Add explicit versioned migrations in future tasks; prefer expand-and-contract.
- Retain the previous release.
- Roll code back without restoring data when schema remains compatible.
- Restore the database only with explicit incident/data-owner approval because
  post-backup writes may be lost.
- Never run two Telegram polling processes during rollout or rollback.

## Secret decisions

- Runtime `.env` remains only on Hostinger, outside Git and release trees.
- Future GitHub Environment secrets contain only minimum deployment credentials;
  runtime application secrets need not transit GitHub.
- Use a dedicated restricted SSH key/account, host-key verification, rotation,
  protected environments and redacted audit logs.

## Migration support

The release architecture preserves v20 as authoritative, introduces new
Observations/Experts/MarketState in shadow hybrid mode, records versioned
comparisons, and promotes capabilities incrementally only after approved parity
and rollback gates.

## Files created

- `docs/architecture/WR-027D_DEPLOYMENT_ARCHITECTURE.md`
- `docs/reports/WR-027D_REPORT.md`

## Files modified

None.

## Production impact

- Production Python changed: **NO**
- Requirements changed: **NO**
- Workflow files added: **NO**
- Deployment scripts added: **NO**
- Secrets or `.env` touched: **NO**
- Hostinger changed: **NO**
- Services restarted: **NO**
- Database touched: **NO**

## Unrelated files preserved

- untracked WR-026C implementation/documents/test: untouched and unstaged;
- untracked WR-027B inventory: untouched and unstaged;
- `docs/chat_archive/`: untouched and unstaged.

## Verification

Before commit:

```bash
git diff --check
git status --short
git diff --cached --name-status
```

Only the two WR-027D Markdown files may be staged. The staged diff must contain
no Python, requirements, workflow, `.env`, secret assignment or unrelated file.
No runtime test or service command is needed for documentation-only work.

## Breaking changes

None.

## Open questions

Host runtime parity, process manager and permissions, database/WAL/backup
requirements, operational owners, recovery objectives, offline smoke checks,
deployment network controls, protection/signing support and hybrid promotion
thresholds require answers before implementation.

## Review gate

Architecture Review is required before merge. CI/CD implementation, Hostinger
changes and deployment require separate explicit tasks and approvals.
