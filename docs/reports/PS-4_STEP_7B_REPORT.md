# PS-4 Step 7B — Reality Gap Contracts and Policy Report

## Result

Finalized the documentation-only contracts and policy architecture for future
deterministic Reality Gap runtime phases. No Python/runtime contract, production
path, Telegram, Hostinger, persistence, learning, Outcome Analysis, dependency,
or deployment change was made.

## Documents created

- `docs/architecture/adr/ADR-PS-4-reality-gap-contracts-policy.md`
- `docs/specs/PS-4-reality-gap-contracts-policy.md`
- `docs/reports/PS-4_STEP_7B_REPORT.md`

The approved Step 7A documents were not materially rewritten and required no
cross-reference change.

## Gap dimensionality decision

Adopted one deterministic `RealityGapPrimaryType` plus an ordered composable set
of `RealityGapDimension` values: MARKET, INTELLIGENCE, OBSERVABILITY,
EXPLANATION, and UNKNOWN. One analysis may contain several dimensions. UNKNOWN
is exclusive of specific dimensions. Primary type describes the dominant
formal divergence and cannot erase secondary system limitations.

This avoids incorrectly forcing a measured market contradiction, a policy
formation limitation, missing provider coverage, and an unresolved explanation
into one mutually exclusive bucket.

## Intelligence Gap taxonomy

Defined DETECTION, INTERPRETATION, CORRELATION, EXPECTATION_FORMATION,
CONFIDENCE_CALIBRATION, POLICY_COVERAGE, and UNKNOWN gaps. A wrong expectation
does not automatically create Intelligence Gap. Classification requires
structured evidence of a system representation/reasoning limitation and may be
blocked by inadequate observability.

## Observability Gap taxonomy

Defined MISSING_PROVIDER_INPUT, STALE_DATA, UNSUPPORTED_FACTOR, PROVIDER_ERROR,
LOW_COVERAGE, POOR_DATA_QUALITY, INSUFFICIENT_EVALUATION_WINDOW,
TIMESTAMP_INCONSISTENCY, IDENTITY_OR_LINEAGE_GAP, and UNKNOWN. Records preserve
source/factor, actual availability, denominator/count/ratio, quality, affected
criteria, and evidence refs. They never infer the hidden market value.

## Explanation Gap

Defined a structured record containing unexplained residual, candidate/evidence
counts, uncovered criteria, limitations, reason, and policy provenance.
Explanation Gap means the formal result is known but eligible evidence does not
adequately explain it. It remains distinct from Observability Gap.

## Root Cause Candidate and Tree decision

Candidates remain plausible explanations, not causal facts. The taxonomy covers
factor weakening/disappearance/non-confirmation/contradiction, stage regression/
stagnation, maturity without confirmation, availability degradation,
observability limitation, intelligence limitation, and unknown.

Roles and dispositions are explicit. Accepted market/intelligence candidates
require temporal precedence and eligible measured support. Equal timestamps are
ambiguous. Rejected/unresolved candidates remain traceable.

The selected structure is an immutable acyclic directed explanatory tree with
multiple roots, deterministic order, one Phase 1 accepted-tree parent per
candidate, policy-controlled depth (proposed 4), alternatives preserved, and
rejected candidates retained outside the accepted tree. Parent-child means
explanatory dependency, not proven causal direction.

## Evidence contract

Defined immutable references for expectation basis, evaluation facts, Timeline
entries, SituationDNA, DNA deltas, stage/availability changes, identity/evolution
traces, and observability facts. Relations and eligibility/rejection reasons are
explicit. Values preserve availability and measured-zero semantics. Evidence
after `evaluated_at`/`window_end` is ineligible and may appear only in rejected
trace facts. Provider payloads, private headers, secrets, and mutable artifact
embedding are forbidden.

## Metric decision

Compared optional uncomputed metrics with conservative deterministic formulas.
Selected versioned Phase 1 formulas because inputs are structured, immutable,
bounded, traceable, and do not claim causality. Runtime calculation remains
deferred to Step 7E; Step 7C contracts may represent metrics as optional until
the calculation phase.

### Unexplained residual

Calculated in the future per unique divergence criterion using maximum
non-overlapping support: 1.0 direct/preceding, 0.5 partial/equal-time ambiguous,
0 unresolved/rejected. Candidate confidences are never summed.

### Explanation Confidence

Architecture-approved metric version 1:

```text
30% evidence coverage
25% temporal-order quality
25% direct criterion relevance
15% independent support
 5% observability quality
- 40% of bounded conflict score
```

It measures explanation support only, not causality, market/trade confidence,
expectation correctness, direction, or profitability.

### Knowledge Gap

Architecture-approved metric version 1:

```text
40% unexplained residual
25% observability deficit
20% candidate conflict
15% explanation-confidence deficit
```

It measures how poorly divergence is explained. Surprise is deliberately
excluded from explanation-quality formulas and may inform severity only. Scores
are bounded 0..100 and future runtime rounds to six decimals after clamping.
Observability Quality is fixed as 70% eligible-evidence coverage plus 30% mean
eligible measured quality. Candidate conflict is the percentage of unique
unordered accepted/partially-supported candidate pairs that structurally
contradict. No missing quality or denominator fallback is allowed.

## Severity decision

Defined NONE/LOW/MEDIUM/HIGH/CRITICAL policy version 1 with deterministic
precedence. CRITICAL requires all of: HIGH expectation, contradictory/mixed
primary type, measured stage impact, high Knowledge Gap or supported specific
Intelligence Gap, and observability quality >= 60. High Surprise alone is never
CRITICAL. An Observability Gap alone is capped at HIGH and reaches HIGH only
when it disables a core capability across the entire window.

Severity means importance to system understanding, never financial/trade risk,
loss, volatility, liquidation, or urgency.

## Decision trace

Defined an immutable ordered trace for source result, evidence eligibility and
rejections, classification steps, candidate generation/disposition, metric
inputs/outputs, severity decisions, unresolved questions, and independent
versions. It stores structured facts and concise reasons, not hidden LLM
reasoning, chain of thought, or prose authority.

## Intelligence Debt boundary

Intelligence Debt remains a future aggregate across many immutable gap records.
One analysis may contribute an immutable Intelligence Gap/debt event, but cannot
own or mutate a cumulative debt score. Aggregation belongs to future memory or
learning analytics and may guide engineering review, never trading behavior.

## Versioning decision

`gap_id` identifies fixed expectation/evaluation/Timeline/evidence-boundary
lineage; `analysis_version` identifies immutable revisions. Later/out-of-window
evidence cannot create a legitimate revision. Defect correction or an approved
policy upgrade may create a new version while preserving all prior records.
Analysis policy, metric, taxonomy, tree, and trace versions are independent.
Deterministic ID algorithms remain Step 7C orchestrator responsibility.

## Production impact

- Python/runtime files: **UNCHANGED**
- Expectation/Evaluation/Timeline/Identity/Evolution contracts: **UNCHANGED**
- Production pipeline/decisions: **UNCHANGED**
- Telegram: **UNCHANGED**
- Hostinger/deployment: **UNCHANGED / NONE**
- Persistence/database: **NONE**
- Learning/Outcome Analysis: **NONE**
- Dependencies: **NONE ADDED**

## Unresolved questions

1. Stable criterion-reference naming for seven rule families.
2. Deterministic IDs for gap/candidate/evidence/tree/trace.
3. Collection size/depth constants beyond proposed tree depth 4.
4. Exact evidence independence/dependency representation.
5. Explicit analysis-version change-reason contract.

## Recommended Step 7C scope

Implement immutable enums and contracts only: deep freezing, validation,
reference resolution, tree integrity, UTC/serialization, version lineage, and
optional metric fields. Do not implement evidence extraction, candidate
generation, classification, tree construction, metric/severity calculations,
or integration. No providers, persistence, Telegram, production, learning,
Outcome Analysis, or deployment.

## Verification

Documentation scope inspection passed. Only the three Step 7B ADR/SPEC/REPORT
files belong to this task. No Python/runtime, existing domain contract,
production, Telegram, deployment, persistence, learning, Outcome Analysis,
dependency, environment, secret, or Hostinger file was modified. Pre-existing
WR-026C, WR-027B, builder, test, and `docs/chat_archive/` files remain untracked
and outside this task.
