# PS-4 Step 7A — Reality Gap Architecture Report

## Result

Defined the documentation-only architecture for a future deterministic Reality
Gap Engine. No Python, production, Telegram, persistence, learning, deployment,
or Hostinger change was made.

## Documents created

- `docs/architecture/adr/ADR-PS-4-reality-gap-engine.md`
- `docs/specs/PS-4-reality-gap-engine.md`
- `docs/reports/PS-4_STEP_7A_REPORT.md`

## Central decisions

### Evaluation is separate from explanation

Expectation Evaluation remains the formal authority for `PENDING`,
`FULFILLED`, `MISSING`, `CONTRADICTED`, `EXPIRED`, or `INDETERMINATE`. Reality
Gap Analysis cannot rewrite that result. It explains why measured expectation
and reality diverged and how well that explanation is supported.

### Reality Gap is a separate immutable layer

The recommended architecture creates a future immutable `RealityGapAnalysis`
from exact immutable expectation/evaluation snapshots and window-bounded
Timeline evidence. The analysis preserves structured gap classification,
events, candidates, evidence, rejections, metrics, provenance, and decision
trace. Rendered prose remains presentation only.

### Root causes remain candidates

The engine may identify deterministic Root Cause Candidates but cannot claim
causal truth. Candidates require measured evidence references, temporal
precedence, criterion relevance, confidence, limitations, and alternatives.
Correlation is not causation, unavailable data is not measured market evidence,
and unresolved explanations remain explicit.

### Observability and explanation are distinct

`OBSERVABILITY_GAP` means reality could not be determined because evidence was
missing, stale, unsupported, erroneous, or insufficient. `EXPLANATION_GAP`
means the formal result is known but available evidence does not adequately
explain it. Future contracts should preserve both dimensions even when one
primary category is required.

### Knowledge Gap differs from Surprise

Surprise Score measures strength of departure from the expectation. Knowledge
Gap measures how poorly the system can explain that departure. High Surprise
can coexist with either low or high Knowledge Gap. No final Knowledge Gap
formula was approved.

### Explanation Confidence has narrow semantics

Explanation Confidence measures support for the proposed explanation based on
completeness, temporal order, direct relevance, independent facts, conflicts,
and observability quality. It is not market/trade confidence, expectation
correctness, direction, or profitability. No final formula was approved.

### Anti-hindsight is mandatory

Only evidence inside the original expectation window and available by
`evaluated_at` is eligible. Stored rule contracts remain authoritative. Current
defaults, later provider facts, future price action, outcomes, and rewritten
history are excluded. A later analysis is a new version, not a mutation.

### Learning and outcome remain downstream

Reality Gap Engine does not learn. Future learning may aggregate immutable gap
records without rewriting them. Reality Gap is also not Outcome Analysis: later
market outcomes over another horizon cannot retroactively alter the original
expectation-window gap.

## Alternatives

The ADR rejects embedding free-form cause text in Evaluation, LLM-generated
causal narratives, and selection of one definitive cause from the largest DNA
delta. It recommends a separate structured Reality Gap layer because that
preserves auditability, multiple candidates, explicit uncertainty, and
anti-hindsight.

## Production impact

- Python/runtime files changed: **NO**
- Expectation/Evaluation contracts changed: **NO**
- Production pipeline/decisions changed: **NO**
- Telegram changed: **NO**
- Hostinger/deployment changed: **NO**
- Persistence/database added: **NO**
- Learning/outcome analysis added: **NO**
- Dependencies added: **NO**

## Unresolved questions

1. Primary type versus orthogonal/composable gap dimensions.
2. Exact evidence relevance rules for all seven Expectation families.
3. Dependency de-duplication among supporting factors.
4. Temporal precedence semantics for equal timestamps.
5. Representation of unexplained residual before metric formulas.
6. Severity thresholds, especially `CRITICAL`.
7. Whether Step 7B should keep Knowledge Gap/Confidence explicitly uncomputed
   or approve deterministic formulas first.
8. Identity/version linkage across later analyses.
9. Availability of stable identity/evolution trace references.
10. Future persistence/retention policy outside Step 7A scope.

## Recommended next phase

PS-4 Step 7B should be a separately reviewed contracts-and-policy design task.
It should finalize immutable model/enums, gap dimensionality, evidence reference
contracts, candidate taxonomy, deterministic decision trace, identity/version
rules, and the explicit metric decision. It must remain process-local and avoid
production, Telegram, persistence, learning, outcome, provider, and deployment
integration.

## Verification

Documentation scope inspection passed. Only the three Reality Gap documents
listed above belong to Step 7A. No Python, production, Telegram, deployment,
secret, environment, dependency, persistence, learning, or Hostinger file was
modified. Pre-existing WR-026C, WR-027B, builder, test, and `docs/chat_archive/`
files remain untracked and outside this task.
