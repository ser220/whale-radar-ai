# PS-4 Step 3 Implementation Report

## Objective

Create a pure deterministic Situation Identity Engine that answers whether one
new Timeline version 1 continues one existing Market Situation Timeline or
represents a new situation. The engine does not update either Timeline and has
no trade, prediction, outcome, persistence, or learning responsibility.

## Base and branch

- Base: `origin/main` at `a5352d0`
- Branch: `ps-4-situation-identity`
- Python: 3.9.6
- PS-4 Step 2 history intentionally excluded because it is not in `origin/main`

## Files changed

- Created `app/intelligence/timeline/identity.py`.
- Updated `app/intelligence/timeline/__init__.py` with identity exports.
- Created `test_situation_identity.py`.
- Created this report.

Approved Timeline models, Early Bird scoring, Emerging Situation stage policy,
scanner, production pipeline, Telegram, requirements, and persistence were not
modified.

## Public API

### SituationIdentityResult

Immutable fields:

- `matched`: whether the candidate continues the existing identity;
- `confidence`: 0–100 identity match-continuity score;
- `reason`: deterministic descriptive explanation;
- `matched_timeline_id` and `matched_version`: present only for a match;
- `candidate_timeline_id`: always preserved;
- `metadata`: deeply immutable rule provenance and criterion scores.

The confidence value is not market confidence, trade confidence, or certainty
about an unmatched decision. It is only the calculated continuity score.
`to_dict()` and `from_dict()` provide deterministic round-trip serialization.

### SituationIdentityEngine

`evaluate(existing_timeline, new_timeline)` accepts one existing non-empty
Timeline and one new Timeline version 1 with exactly one entry. It returns a
result and never mutates or replaces either input.

Configuration:

- default maximum time gap: 6 hours;
- default soft-match threshold: 65.0;
- both values are validated and may be supplied explicitly to the constructor.

## Hard rejection rules

Hard rejection executes before continuity scoring and returns match confidence
`0.0`:

1. assets differ;
2. the existing Timeline stage is `EXHAUSTED`;
3. the existing Timeline is explicitly closed;
4. the candidate entry predates the existing Timeline state;
5. the configured maximum time gap is exceeded.

The approved Timeline model has no dedicated closed field. Phase 1 therefore
recognizes only explicit metadata markers: `closed is True` or
`status == "CLOSED"` (case-insensitive). Other truthy values do not close a
Timeline. This is a provisional compatibility boundary, not persistence state.

## Soft continuity rules

Soft scoring is deterministic and contains no fuzzy matching, ML, embeddings,
vector search, or external data:

| Criterion | Weight | Rule |
| --- | ---: | --- |
| Time continuity | 0.10 | linear from 100 at zero gap to 0 at the configured maximum |
| Stage compatibility | 0.15 | exact/one-step progression 100; two-step 70; one-step regression 55; UNKNOWN 50; other jump 20 |
| DNA continuity | 0.30 | 60% mean score continuity on shared measured factors plus 40% availability-set overlap |
| Supporting-factor continuity | 0.15 | exact Jaccard overlap |
| Limiting-factor continuity | 0.05 | exact Jaccard overlap |
| Evolution continuity | 0.25 | mean `100 - absolute delta` for emergence, horizon, detection confidence, opportunity, priority, and maturity |

Only factors measured in both DNA snapshots contribute to their score
continuity. Missing or unsupported values never become measured zero. Empty
factor sets contribute no overlap evidence. The weighted result is bounded to
0–100 and compared with the configured threshold.

## Deterministic explanations

Hard rejections return a fixed reason and explicit rejection code. Soft results
report whether the threshold was met together with total continuity, DNA,
stage, and supporting-factor scores. Metadata preserves every criterion,
weight, policy version, threshold, stages, and time gap for auditability.

## Verification

- Python 3.9 compile: PASS.
- Situation Identity focused tests: 24 passed.
- Timeline, Early Bird, Market Situation, and intelligence regressions:
  373 passed (397 unittest checks total).
- Safe smoke scripts: 3 passed.
- Dependency-boundary audit: PASS.
- Input immutability and deterministic output: PASS.
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

- Should a future Timeline contract introduce an explicit closure state instead
  of the provisional metadata marker?
- Which reviewed calibration process may change the six-hour window, threshold,
  or criterion weights without turning the engine into learning?
- Which future orchestrator will compare one candidate against multiple active
  timelines while preserving deterministic ordering?
- After PS-4 Step 2 is reviewed and merged, which layer will apply a positive
  identity result through append-only Timeline replacement?
