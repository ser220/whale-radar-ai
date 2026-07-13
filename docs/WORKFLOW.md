# Whale Radar AI engineering workflow

## Ownership model

- The ChatGPT browser conversation is the Architecture Owner / Chief Architect.
- Codex is the Implementation Owner / Lead Developer.
- GitHub stores reviewed implementation history.
- The existing production pipeline remains operational unless an approved architecture task explicitly changes it.

## Required lifecycle

```text
ARCHITECTURE APPROVED
→ REPOSITORY INSPECTION
→ IMPLEMENTATION
→ COMPILE CHECK
→ FOCUSED TESTS
→ SAFE EXISTING TESTS
→ REPORT
→ FEATURE-BRANCH COMMIT
→ PUSH FEATURE BRANCH
→ ARCHITECTURE REVIEW
→ MERGE APPROVAL
```

## Working-tree policy

Before implementation, inspect the current branch, status, remotes, and recent
history. Preserve all pre-existing work. Keep unrelated changes outside the WR
commit, and never discard, reset, stash, or overwrite them without explicit
approval.

## Branch and commit policy

Architecture work uses a dedicated feature branch. Stage only files belonging
to the approved task and its workflow documentation. Never merge directly into
`main`, never force-push, and never commit when a required check fails.

## Verification policy

Compile every created or modified Python file, run focused tests, run safe
existing local checks, audit dependency boundaries, confirm production paths
were not modified unintentionally, and inspect the diff before staging. Tests
that send real messages or require live services are excluded unless explicitly
authorized.

## Review policy

Every WR task produces a report in `docs/reports/`. A pushed feature branch must
wait for Architecture Review and explicit merge approval. Codex does not begin
the next WR task automatically.
