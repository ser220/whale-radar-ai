# ADR: PS-4 Reality Gap Engine Architecture

## Status

Proposed; awaiting Architecture Review.

## Context

Whale Radar AI can record an immutable `SituationExpectation` before its
evaluation window and later produce an immutable
`SituationExpectationEvaluation`. Evaluation classifies the formal result as
pending, fulfilled, missing, contradicted, expired, or indeterminate. That
classification does not explain why expected and observed reality diverged.

A future Reality Gap layer must answer:

1. What happened that should not have happened?
2. What did not happen that should have happened?
3. Which measured facts plausibly explain the gap?
4. How important is the gap to the system's market understanding?
5. How confidently can the system explain it?

The analysis must remain reproducible, availability-aware, non-causal by
default, and protected from hindsight. It must not become trading logic,
outcome analysis, learning, or free-form narrative generation.

## Decision

Create a future separate structured Reality Gap Analysis layer after
Expectation Evaluation:

```text
SituationExpectation
        +
SituationExpectationEvaluation
        +
Window-bounded Timeline evidence
        ↓
RealityGapEngine
        ↓
Immutable RealityGapAnalysis
```

The engine will consume immutable records and emit a new immutable analysis. It
will never mutate expectation, evaluation, Timeline, identity/evolution trace,
or a prior gap analysis.

`RealityGapAnalysis` will preserve stable identity and provenance, conceptual
gap type and severity, Knowledge Gap Score, Explanation Confidence, event
groups, root-cause candidates, supporting evidence, rejected explanations,
source snapshots, source Timeline versions, a deterministic decision trace,
and versioned policy metadata. Exact Python field types and scoring formulas
remain subject to Step 7B review.

## Reality Gap versus Evaluation

Expectation Evaluation answers: **What was the formal result?**

Reality Gap Analysis answers: **Why did expectation and measured reality appear
to diverge, and how well can the system explain that divergence?**

Examples:

- `MISSING`: volume confirmation did not occur. Gap analysis may identify
  measured structure weakening and rising maturity as plausible explanations.
- `CONTRADICTED`: expected stage advance failed. Gap analysis may identify
  measured momentum collapse and stage regression.
- `FULFILLED` with unexpected events: the expected factor appeared, but another
  strong initiating factor became unavailable.
- `EXPIRED`: the formal expectation could not be assessed. Gap analysis should
  normally classify an observability gap, not invent market causes.

Evaluation status, evaluation gap type, and Surprise Score remain authoritative
inputs. Reality Gap Analysis cannot rewrite them.

## Conceptual gap categories

- `NO_GAP`: expected and observed reality align without material unexplained
  divergence.
- `MISSING_EXPECTED_REALITY`: a sufficiently observed expected event did not
  occur.
- `UNEXPECTED_REALITY`: a material measured event outside the expectation
  occurred.
- `CONTRADICTORY_REALITY`: measured reality satisfied explicit contradiction
  criteria.
- `MIXED_GAP`: more than one missing, unexpected, or contradictory dimension is
  materially present.
- `OBSERVABILITY_GAP`: data remained missing, stale, unsupported, erroneous, or
  otherwise insufficient to determine what happened.
- `EXPLANATION_GAP`: the expectation result is known, but available measured
  evidence cannot adequately explain why.
- `UNKNOWN`: classification itself is not reliable enough.

`OBSERVABILITY_GAP` and `EXPLANATION_GAP` are distinct. The first means reality
could not be observed adequately. The second means reality was classified but
the available evidence does not explain it. A record may preserve both as
separate dimensions even if Phase 1 exposes one primary gap type.

## Root Cause Candidate semantics

The layer records **Root Cause Candidates**, never Root Cause Facts. Each
candidate should contain:

- deterministic cause category;
- references to immutable measured evidence;
- evidence timestamp and temporal precedence relative to the gap;
- direct relevance to a failed, unexpected, or contradictory criterion;
- confidence and limitations;
- alternative explanations and conflicts;
- analysis-policy version.

Candidate categories may include weak volume confirmation, momentum
deterioration, structure weakening, factor availability loss, stage regression,
maturity increase without confirmation, initiating-factor disappearance, and
insufficient data coverage.

Rules:

1. Correlation is not causation.
2. Temporal precedence is required for an explanatory candidate.
3. Unavailable data may explain an observability gap but cannot be a measured
   market cause.
4. Lack of evidence is explicit, never converted to neutral or zero.
5. Multiple candidates may coexist.
6. Conflicting candidates reduce Explanation Confidence.
7. The engine may conclude that no supported explanation exists.
8. Prose summarizes structured candidates; prose is not source of truth.

## Knowledge Gap Score

Knowledge Gap Score means: **How poorly can the system explain the observed
expectation/reality difference?** It is separate from Surprise Score, which
means how strongly reality departed from the structured expectation.

Candidate inputs are:

- evaluation status, evaluation gap type, and Surprise Score;
- evidence coverage and observability quality;
- number, independence, relevance, and strength of root-cause candidates;
- disagreement among candidates;
- unexplained residual gap;
- rejected explanations and why they were rejected.

High Surprise with low Knowledge Gap means the divergence was strong but
measured evidence explains it well. High Surprise with high Knowledge Gap means
the divergence was strong and poorly explained. Low Surprise with high
Knowledge Gap remains possible when a small miss is difficult to explain.

No formula is approved in this ADR. Step 7B must propose a bounded,
deterministic, monotonic formula with explicit missing-data semantics and golden
tests before implementation.

## Explanation Confidence

Explanation Confidence means: **How strongly measured evidence supports the
proposed explanation.** It is not market confidence, trade confidence,
expectation correctness, direction probability, or probability of profit.

Candidate inputs are evidence completeness, temporal ordering, criterion
relevance, independent supporting facts, candidate conflict, and observability
quality. Confidence must fall when evidence is unavailable, temporally late,
indirect, dependent, or contradictory. A high score requires direct measured
evidence that precedes and relates to the classified gap.

## Severity

Conceptual levels are `NONE`, `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL`. Severity
means importance of the divergence to the system's market understanding. It is
not financial loss, volatility, trade risk, liquidation risk, or execution
urgency.

Candidate inputs include expectation strength, evaluation status, Surprise
Score, number of missing/contradictory criteria, stage/factor impact, persistence
of the gap, and observability limitations. No final mapping or formula is
approved here.

## Evidence policy and boundaries

The future engine may use only:

- the immutable expectation snapshot and stored evaluation contract;
- the immutable evaluation record;
- Timeline entries and SituationDNA deltas created inside the evaluation window
  and no later than `evaluated_at`;
- identity/evolution traces already preserved for those Timeline versions;
- stable references to measured evidence.

It must not use future price action, later outcomes, evidence outside the
window, provider data fetched after evaluation, current policy defaults,
rewritten history, arbitrary external context, or LLM-generated causal guesses.
Availability states remain evidence provenance, not directional market facts.

## Anti-hindsight guarantees

1. Every analysis links exact expectation, evaluation, Timeline, and policy
   identities.
2. Only evidence available at or before `evaluated_at` is eligible.
3. Window boundaries from the source expectation remain authoritative.
4. Later evidence may create a separately versioned analysis but never rewrite
   an earlier one.
5. Stored rule contracts cannot be replaced by current policy defaults.
6. Structured evidence/candidates are authoritative; rendered text is not.
7. Outcome knowledge is excluded unless a separate future outcome-analysis
   phase explicitly links it without rewriting the gap.
8. Rejected candidates and unexplained residuals remain auditable.

## Deterministic decision trace

Every future analysis must preserve an ordered trace containing:

1. source expectation and evaluation result;
2. primary/secondary gap classification;
3. exact evidence window and eligible Timeline versions;
4. cause candidates considered;
5. accepted candidates and evidence references;
6. rejected candidates and rejection reasons;
7. conflicts, observability limitations, and unexplained residual;
8. Explanation Confidence and Knowledge Gap inputs;
9. final severity;
10. policy and contract versions.

The trace must be deterministic for identical input snapshots and policy.

## Learning boundary

Reality Gap Engine does not learn, optimize, recalibrate, or mutate policy. It
produces structured records that a separately reviewed learning layer may later
aggregate. Learning may study recurring missing expectations, cause candidates,
observability failures, or Surprise/Confidence relationships, but it must never
rewrite historical gap analyses.

## Outcome boundary

Reality Gap Analysis is not Outcome Analysis. It compares expectation and
observed reality only inside the expectation window. Outcome Analysis may later
evaluate the broader situation over another horizon. A large move three hours
after a missed 60-minute confirmation does not retroactively fulfill or erase
the earlier gap.

## Architectural principles

1. Evaluation is not explanation.
2. Identity is not similarity.
3. Correlation is not causation.
4. Missing data is not market evidence.
5. Surprise is not ignorance.
6. A causal explanation may remain unresolved.
7. Historical records are never rewritten.
8. Learning consumes Gap Analysis; Gap Analysis does not learn.
9. Outcome does not retroactively alter expectation-window reality.
10. Structured evidence is authoritative; prose is presentation only.

## Alternatives considered

### A. Add root-cause text to Expectation Evaluation

Rejected. It mixes formal classification with explanation, encourages mutable
narrative, and cannot preserve structured candidates or rejected alternatives.

### B. Use an LLM for free-form explanations

Rejected. Free-form generation is not deterministic evidence and can invent
causal relationships. A future presentation layer may summarize structured
analysis but cannot create evidence or candidates.

### C. Infer one definitive cause from the largest DNA delta

Rejected. Magnitude alone does not establish relevance, independence, temporal
precedence, or causation, and it hides alternative explanations.

### D. Create a separate structured Reality Gap Analysis layer

Accepted. It preserves separation of concerns, auditability, explicit
uncertainty, multiple candidates, anti-hindsight, and future learning inputs.
Trade-offs are additional models/policy/versioning, more conservative unresolved
results, and higher test/documentation burden.

## Future implementation phases

1. **Step 7B — Contracts and policy proposal:** finalize immutable models,
   enums, evidence references, trace structure, deterministic ID/versioning,
   and justified formulas or leave scores explicitly uncomputed.
2. **Step 7C — Deterministic classification:** implement gap classification,
   candidate extraction, rejection reasons, and fixed-time tests without
   persistence.
3. **Step 7D — Explanation metrics:** implement reviewed Knowledge Gap,
   Explanation Confidence, and severity formulas with golden tests.
4. **Later integration:** optional process-local orchestration, then separately
   reviewed persistence/UI/learning/outcome consumers. No production influence
   is implied by this ADR.

## Out of scope

Python models/engine, formulas, Timeline changes, persistence, Telegram UI,
learning, outcome analysis, pattern similarity, LLM causal explanation,
provider calls, production integration, deployment, and Hostinger changes.
