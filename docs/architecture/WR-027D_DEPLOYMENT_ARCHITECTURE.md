# WR-027D — GitHub ↔ Hostinger Deployment Architecture

## Status and scope

Proposed architecture for review. This document designs a safe deployment
model; it does not implement automation, scripts, workflows, migrations,
containers, service changes, or Hostinger changes.

Known state:

- Hostinger runs the live Telegram bot from reported commit `d2182d2` and the
  v20 production architecture.
- GitHub contains the reviewed intelligence foundation through
  `v0.8-first-expert` plus later architecture work.
- Repository and deployed runtime parity has not been established.

No deployment is permitted from this design alone.

## Current state

```text
Developer machine
    |
    v
GitHub
    |
    X  no reproducible release/deployment boundary
    |
Hostinger live runtime
```

GitHub and Hostinger are different histories. The server is currently both a
runtime and an unknown source of deployment truth. A Git commit reported by a
server is not sufficient parity evidence when its files, dependencies, Python
version, database schema, environment and service definition have not been
compared with the repository.

### Why the current model is unsafe

- Manual server edits are not reviewed, tested, attributable, or reliably
  reproducible. A later checkout can silently overwrite them.
- Copying GitHub over production can remove host-only files that make the live
  bot work, including currently unresolved `/analyze` modules.
- A partial copy can mix incompatible versions in one Python process.
- Secrets in source control remain in Git history after deletion and can be
  exposed through clones, logs, reviews and artifacts.
- SQLite combines schema and production data in one file. Code rollback does
  not automatically reverse a schema change, while database restore can lose
  writes made after its backup.
- An unmanaged restart can interrupt Telegram polling or webhook processing and
  leave the actual running version ambiguous.

Therefore production must first be inventoried and made reproducible. It must
not be overwritten merely to make the checked-out commit appear current.

## Target state

GitHub becomes the only source of application code and release history.
Hostinger becomes a deployment target containing immutable releases plus
explicitly shared runtime state.

```text
Developer
    v
Feature branch
    v
Automated and required tests
    v
Architecture review
    v
Protected main
    v
Release candidate
    v
Approved immutable release tag
    v
Controlled deployment
    v
Hostinger verification
    v
Telegram bot
```

### Deployment gates

| Gate | Required evidence | Owner/approval | Failure behavior |
| --- | --- | --- | --- |
| Feature branch | Scoped change, report, no secrets, backward compatibility | Implementer | Remain on branch |
| Tests | Compile, focused tests, safe regression suite, migration checks when relevant | Automated runner + implementer | No review/merge |
| Architecture review | Boundaries, production impact, rollback and operational risk accepted | Architecture reviewer | Changes requested |
| Protected `main` | Reviewed history merged without rewriting; required checks green | Authorized maintainer | No release candidate |
| Release candidate | Exact commit, dependencies and migration plan frozen; artifact provenance recorded | Release owner | Candidate rejected, `main` unchanged |
| Deployment approval | Backup verified, maintenance/rollback plan ready, secrets available, prior release healthy | Production approver | No host mutation |
| Hostinger verification | Exact commit, import/smoke/health checks, service status and Telegram/webhook health | Deployer + production approver | Roll back immediately |

The deployable identity is an immutable commit and signed/annotated release tag,
not a branch name alone. Deployment records must capture tag, commit, operator,
time, checks, database migration version and rollback target.

## Branch and release strategy

### `main`

- Purpose: stable, reviewed, releasable code.
- Protected from direct pushes and force pushes.
- Only authorized maintainers merge after required checks and Architecture
  Review for architecture/runtime changes.
- Merge does not itself deploy.

### `feature/*`

- Purpose: isolated implementation or documentation work.
- Existing `wr-*` task branches are the current equivalent and may retain their
  naming convention.
- Authors may push; merge requires review and green required checks.
- Never used as a production checkout.

### `production-v20`

- Purpose: protected archival branch identifying the verified legacy baseline.
- It should be created only after Hostinger parity proves what v20 actually is.
- It is not a development branch and does not receive new features.
- An immutable `v20-production-baseline`-style tag should identify the exact
  verified baseline; branch movement requires production-owner approval and an
  audit record.

### `release/*`

- Purpose: short-lived stabilization branch for an approved deployment
  candidate when a release needs fixes without admitting unrelated `main`
  changes.
- Created from a specific reviewed `main` commit.
- Accepts only reviewed release fixes; fixes also return to `main` through
  normal review so histories do not diverge.
- Deployment uses the final tag, not the mutable release branch.

### Merge, deployment and rollback authority

- Code owners/authorized maintainers merge.
- A designated production approver authorizes deployment separately.
- The deployer operates with a restricted deployment account, not a personal
  root session.
- Rollback is authorized by the production incident owner or automatically by
  pre-approved health thresholds once automation is introduced.
- No force-push, rewritten reviewed history, or unreviewed server commit is part
  of the model.

## Desired Hostinger model

Hostinger should contain:

```text
/srv/whale-radar/
  releases/<release-id>/       immutable checked-out application release
  current -> releases/<id>/    atomically switched active release
  shared/env/                  protected environment configuration
  shared/data/                 production SQLite database
  shared/backups/              access-controlled database backups
  shared/logs/                 logs when not using the service journal
```

Exact paths are illustrative and require host verification.

Each release has an isolated virtual environment or a reproducible immutable
dependency environment tied to that release. `current` changes only after the
candidate is prepared and preflight checks pass. The previous release remains
present for code rollback.

The environment file and production database live outside the Git checkout and
are referenced explicitly by the service configuration. Permissions allow the
service user only the access it needs. A service manager such as systemd owns
start, stop, restart, environment loading, working directory, automatic restart
policy and status. Logs go to the service journal or a controlled shared log
directory with retention and secret redaction.

Hostinger must not:

- be used to develop or commit application code;
- contain manual patches to tracked Python files;
- use `git pull` directly in the live working tree as the deployment protocol;
- store `.env`, database, logs, virtual environments or backups in Git;
- run deployment as root when a restricted account can perform it;
- discard the previous release before post-deployment verification succeeds.

Emergency server changes require incident authorization, an audit record, and
an immediate equivalent reviewed Git change. The preferred response is rollback,
not an undocumented patch.

## Deployment approach comparison

| Option | Complexity | Security | Rollback | Maintenance | Whale Radar AI suitability |
| --- | --- | --- | --- | --- | --- |
| **A. Manual controlled deployment** | Low–medium; documented checklist and named operator | Good if SSH keys, least privilege and approvals are enforced; human error remains | Good with immutable release directories and explicit previous-release pointer | Manual effort and consistency burden | **Safest immediate transition** while parity, service ownership and DB behavior are unknown |
| **B. GitHub Actions SSH deployment** | Medium; protected environment, workflow, deploy command and verification required | Strong when using a dedicated restricted key, pinned actions, protected environment approvals and minimal secrets; workflow/supply-chain risk must be managed | Strong and repeatable after release layout and rollback command are proven | Lower routine effort; workflow and runner dependencies require upkeep | **Recommended target** after Option A has proven the runbook and parity |
| **C. Self-hosted deployment agent** | High; runner lifecycle, queue, isolation and host hardening | Highest host exposure because repository jobs execute near production; requires rigorous isolation | Can be strong but agent failure expands incident scope | Highest operational burden, patching and monitoring | Not justified for current single-host maturity |

### Recommendation

Use **Option A first**, not as ad-hoc copying but as a versioned, approved
runbook operating immutable releases. It minimizes new moving parts while the
actual Hostinger state is unknown. After at least one non-production rehearsal
and controlled release/rollback prove the model, implement **Option B** as the
target CI/CD mechanism in a separate reviewed task. Do not install a self-hosted
agent on the production host at current maturity.

## Manual controlled deployment lifecycle (design only)

1. Select an annotated release tag whose commit is on protected `main`.
2. Verify required checks and Architecture Review references.
3. Record current release, service health, Python/dependency identity, database
   schema version and rollback target.
4. Create and verify a consistent SQLite backup outside the release directory.
5. Materialize a new release directory from the exact tag; do not update the
   active directory in place.
6. Build its isolated environment from pinned dependencies.
7. Run offline import/compile/configuration preflight without starting a second
   Telegram poller or sending messages.
8. If migrations are approved, enter the defined maintenance boundary, verify
   the backup again, run the exact versioned migration and validate schema.
9. Switch `current` atomically, restart through the service manager, and verify
   process, commit, logs, webhook health and Telegram behavior.
10. If any mandatory check fails, execute the rollback plan. Otherwise record
    the successful release and retain the prior release/backup per policy.

This sequence is not a deployment script and grants no deployment permission.

## Database safety strategy

### Placement and ownership

- Keep SQLite in `shared/data`, never inside a release checkout.
- Record an explicit schema version; do not infer compatibility from table
  existence or catch-and-ignore `ALTER TABLE` errors indefinitely.
- Restrict filesystem access to the service and backup/deployment roles.

### Before every deployment

- Identify whether the release changes schema or data semantics.
- Create a transactionally consistent SQLite backup using a SQLite-aware online
  backup method, or stop writes inside an approved maintenance window. A raw
  file copy is unsafe while writes/WAL activity are possible.
- Include required WAL state or checkpoint safely according to the selected
  backup method.
- Validate backup integrity and restoration in a non-production location.
- Record checksum, timestamp, schema version, release ID and retention expiry;
  do not put the database or backup in Git or general workflow artifacts.

### Schema changes

- Use numbered, deterministic, idempotency-aware migrations reviewed with the
  application change.
- Prefer expand-and-contract: add backward-compatible structures first, deploy
  readers/writers, backfill separately, then remove old structures only in a
  later release after rollback no longer depends on them.
- Define forward and backward application compatibility for every migration.
- Destructive or irreversible migrations require a maintenance window, tested
  restore, explicit data owner approval and a longer rollback decision.

### Rollback implications

Code rollback is safe only if the old code can read the current schema. If it
can, switch to the prior release without restoring the database. If it cannot,
database restore may be necessary and will discard writes after the backup.
The incident owner must explicitly choose between downtime/data reconciliation
and point-in-time restore. Never restore automatically merely because a service
health check failed.

## Secret management

- Production `.env` stays only on Hostinger in protected shared configuration,
  outside Git and outside release directories.
- Application secrets, API keys, Bot token, chat destination and webhook secret
  are never committed, printed, copied into release artifacts or stored in
  database backups unless intrinsically part of encrypted data.
- GitHub Actions, when implemented, uses protected GitHub Environment secrets
  only for deployment credentials and any minimum required release metadata.
  Application runtime secrets need not pass through GitHub when they already
  reside on Hostinger.
- Use a dedicated SSH deploy key/account restricted by user, file permissions,
  command/sudo policy and network controls. Do not share a developer key.
- Prefer short-lived credentials where Hostinger supports them. Otherwise
  rotate on schedule and immediately after personnel, repository or incident
  changes.
- Rotation process: provision new secret, validate without exposure, switch the
  service, revoke old secret, verify, and record actor/time/secret identifier
  (never the value).
- Secret scanning is a required repository gate. Logs and failure messages must
  redact headers, tokens, cookies, `.env` content and private payloads.

## Rollback strategy

### Precondition

Every release has a recorded previous release, compatible database decision,
verified backup, service command, health checks and responsible incident owner.

### Failure procedure

1. Stop the rollout and prevent additional instances from starting. Never run
   two Telegram polling consumers unintentionally.
2. Preserve the failed release, logs and deployment record for investigation;
   do not patch it in place.
3. If schema-compatible, atomically repoint `current` to the previous release
   and restore service through the service manager.
4. Verify one healthy process, expected commit, database access, webhook health,
   Telegram polling/message behavior and absence of repeated failures.
5. Restore the database only when required by incompatibility/corruption and
   explicitly approved after evaluating post-backup data loss. Validate the
   restored database before service start.
6. Keep production on the previous release, open an incident/review, and fix
   forward on a feature branch. Do not retry blindly.

Rollback success criteria and maximum decision time must be defined before the
first real deployment. A release is not complete until rollback remains viable.

## Supporting the v20 → Intelligence migration

```text
v20 production (authoritative legacy decisions)
    v
hybrid mode (legacy authoritative + new Experts in shadow)
    v
new Intelligence architecture (after approved parity gates)
```

### v20 preservation

- Capture the exact verified v20 baseline on `production-v20` and an immutable
  tag after parity audit.
- Keep its release directory and database compatibility available.
- Add characterization tests before changing behavior.

### Hybrid mode

- Legacy modules remain active and authoritative.
- Observations, Experts, MarketStateEngine and future Decision components run
  in shadow without sending alerts or changing readiness.
- Store versioned comparison results and data health, not raw secrets/provider
  payloads.
- Compare direction, confidence, readiness stage, alert eligibility, latency,
  missing evidence and failure behavior across a pre-approved observation
  period.
- A new component failure degrades shadow output only; it cannot stop the live
  v20 alert path.

### Intelligence rollout

- Promote one bounded capability at a time through a reviewed feature flag or
  equivalent configuration.
- Release candidate records the exact legacy/new policy versions.
- Canary scope, observation window and rollback thresholds are approved before
  each promotion.
- Preserve the legacy release until full production acceptance and data
  retention requirements are satisfied.

## Security checklist

- [ ] Dedicated SSH key authentication; password login not used for deployment.
- [ ] Dedicated non-root deploy and service users with least privilege.
- [ ] Narrow sudo/command permissions; no general root shell when avoidable.
- [ ] Host key verification pinned; no disabled SSH verification.
- [ ] Protected `main`, release tags and GitHub deployment environment.
- [ ] Required tests, reviews and explicit production approval.
- [ ] Pinned dependencies and, for future workflows, pinned action revisions.
- [ ] `.env` and runtime secrets outside Git/releases with restrictive modes.
- [ ] Repository, log and artifact secret scanning/redaction.
- [ ] SQLite-aware backup plus tested restore before schema changes.
- [ ] Previous immutable release retained and rollback rehearsed.
- [ ] Service manager owns lifecycle; exactly one polling bot instance.
- [ ] Deployment, migration, restart, verification and rollback audit trail.
- [ ] Log retention, rotation, access control and incident correlation IDs.
- [ ] No production database, `.env`, logs, backups or venv in Git/artifacts.

## CI/CD target recommendation

After parity and manual runbook rehearsal, create a separate reviewed GitHub
Actions design with two distinct workflows/gates:

1. **Validation:** runs on branches/PRs without production secrets.
2. **Release/deployment:** runs only for approved immutable tags, uses a
   protected GitHub Environment with required reviewer, connects as restricted
   deploy user, invokes one narrowly scoped host-side release operation, and
   records verification/rollback result.

The future workflow must not SSH arbitrary repository commands as root, expose
runtime `.env`, run from untrusted pull requests, or deploy every merge to
`main`. This task creates no workflow.

## Open questions and prerequisites

1. What exact files, commit, Python version, dependencies, service definitions,
   working directory and process user are live on Hostinger?
2. Which host-only files explain the repository `/analyze` import gap, and are
   they authoritative or obsolete?
3. Which service manager and SSH restrictions are supported by the Hostinger
   plan and current account privileges?
4. Where is the production SQLite database, is WAL enabled, how large is it,
   and what maintenance window/write volume must backup support?
5. What backup destination, encryption, retention, restore-time objective and
   acceptable data-loss objective are required?
6. Who may merge, approve a release, deploy, declare an incident and authorize
   database restore?
7. What offline smoke checks can validate Telegram/webhook configuration
   without sending messages or starting a second poller?
8. What health thresholds and observation duration permit automatic rollback
   or promotion from hybrid mode?
9. Are signed tags/commits and GitHub branch/environment protection available
   and configured for this repository?
10. Must deploy traffic pass through a fixed allowlist/VPN, or is restricted SSH
    sufficient for the current host?

These questions must be answered before CI/CD implementation or production
deployment.

## Out of scope

- GitHub Actions or any workflow file;
- deployment/rollback/backup scripts;
- Docker or Kubernetes;
- Hostinger, SSH, service-manager or firewall changes;
- database migrations or schema changes;
- runtime code, adapters, contracts or Intelligence integration;
- deployment of any commit.
