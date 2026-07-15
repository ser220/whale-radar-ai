# ADR: PS-4 Reality Gap Contracts and Policy

## Status

Proposed; awaiting Architecture Review.

## Context

PS-4 Step 7A approved a separate Reality Gap Analysis layer that explains why
an immutable expectation and measured reality diverged. It separated formal
Expectation Evaluation from explanation, prohibited hindsight and definitive
causal claims, and distinguished Surprise, Knowledge Gap, Explanation
Confidence, observability, learning, and outcome analysis.

Step 7B must make that boundary implementable without adding runtime code. The
future contracts need composable dimensions because a single analysis may
contain a measured market divergence, a limitation in system intelligence, an
observability failure, and an unresolved explanation simultaneously. They also
need stable evidence references, candidate dispositions, an immutable
explanatory graph, transparent metrics, deterministic severity, independent
version identities, and a structured audit trace.

## Decision

Adopt a versioned family of immutable conceptual records:

- `RealityGapAnalysis` as the aggregate record for one expectation/evaluation
  lineage and one immutable analysis version;
- `RealityGapEvidenceReference` as a stable reference to eligible structured
  evidence, never an embedded mutable artifact or provider payload;
- `RootCauseCandidate` as a plausible explanation with explicit evidence,
  limitations, alternatives, role, and disposition;
- `RootCauseTree` as an immutable acyclic directed explanatory structure that
  permits multiple roots and alternatives;
- `ExplanationGapRecord`, `IntelligenceGapRecord`, and
  `ObservabilityGapRecord` as structured dimension details;
- `RealityGapDecisionTrace` as the authoritative ordered record of inputs,
  rejections, decisions, metrics, severity, and versions;
- `RealityGapMetricInputs` and `RealityGapSeverityInputs` as explicit computed
  inputs so final scores never hide their basis.

All fields and formulas in this ADR are architecture contracts for later
implementation. Step 7B adds no Python runtime model or calculation.

## Composable gap dimensions

Use `RealityGapDimension`:

- `MARKET`
- `INTELLIGENCE`
- `OBSERVABILITY`
- `EXPLANATION`
- `UNKNOWN`

Use one `RealityGapPrimaryType` for the dominant formal divergence:

- `NO_GAP`
- `MISSING_EXPECTED_REALITY`
- `UNEXPECTED_REALITY`
- `CONTRADICTORY_REALITY`
- `MIXED_GAP`
- `OBSERVABILITY_GAP`
- `EXPLANATION_GAP`
- `UNKNOWN`

The primary type is singular and deterministic. Dimensions are an ordered,
duplicate-free set and may coexist. `UNKNOWN` cannot coexist with a more
specific dimension. Primary type does not erase secondary dimensions.

Examples:

- `FULFILLED` plus unrelated unexpected event: primary
  `UNEXPECTED_REALITY`, dimensions `MARKET` and possibly `EXPLANATION`.
- `EXPIRED` because funding remained unsupported: primary
  `OBSERVABILITY_GAP`, dimension `OBSERVABILITY`.
- measured stage contradiction with inadequate rule formation: primary
  `CONTRADICTORY_REALITY`, dimensions `MARKET` and `INTELLIGENCE`.
- known missing confirmation with no supported cause: primary
  `MISSING_EXPECTED_REALITY`, dimensions `MARKET` and `EXPLANATION`.

Absence of evidence does not itself create `INTELLIGENCE`. Intelligence gaps
require structured evidence about system representation or reasoning.

## Market, Intelligence, Observability, and Explanation

### Market Gap

Describes measured reality relative to the stored expectation: missing expected
events, unexpected events, contradictions, or their mixture. It never describes
hidden values for unavailable factors.

### Intelligence Gap

Describes an evidenced limitation in detection, structured interpretation,
correlation, expectation formation, confidence calibration, or approved policy
coverage. A wrong expectation alone is insufficient.

### Observability Gap

Describes inability to measure relevant facts reliably within the original
window. It preserves source/factor, availability state, denominator, ratio,
quality, and timestamp limitations without inferring market meaning.

### Explanation Gap

Describes a known formal result whose divergence remains materially unexplained
after eligible candidates are evaluated. It records unexplained residual,
candidate conflicts, evidence/candidate counts, limitations, and reason.

## Intelligence Gap taxonomy

Use `IntelligenceGapType`:

- `DETECTION_GAP`: eligible measured evidence existed but was absent from the
  source situation or expectation basis.
- `INTERPRETATION_GAP`: represented evidence was structurally interpreted in a
  way inconsistent with later measured development.
- `CORRELATION_GAP`: relevant measured facts existed but were not linked or
  jointly considered.
- `EXPECTATION_FORMATION_GAP`: the stored rule/contract was inadequate despite
  sufficient source observation.
- `CONFIDENCE_CALIBRATION_GAP`: expectation strength or system confidence
  materially exceeded justified source coverage/quality.
- `POLICY_COVERAGE_GAP`: no approved rule represented a recurring measurable
  expectation class.
- `UNKNOWN`: evidence supports an intelligence limitation but cannot distinguish
  the subtype.

Each `IntelligenceGapRecord` must reference the source reasoning artifact,
omitted/misused evidence, exact policy/rule version, concise reason, confidence,
limitations, and evidence refs. Observability limitations may prevent a
specific intelligence classification.

## Observability Gap taxonomy

Use `ObservabilityGapType`:

- `MISSING_PROVIDER_INPUT`
- `STALE_DATA`
- `UNSUPPORTED_FACTOR`
- `PROVIDER_ERROR`
- `LOW_COVERAGE`
- `POOR_DATA_QUALITY`
- `INSUFFICIENT_EVALUATION_WINDOW`
- `TIMESTAMP_INCONSISTENCY`
- `IDENTITY_OR_LINEAGE_GAP`
- `UNKNOWN`

Each `ObservabilityGapRecord` must preserve expected factor/source, actual
availability, evidence window, eligible denominator, measured count/ratio,
quality when known, affected criteria, and limitations. `UNSUPPORTED_FACTOR`
is a capability fact and remains distinct from temporary absence/error.
Equal-timestamp ambiguity is explicit. No record may infer the hidden market
value.

## Explanation Gap contract

An `ExplanationGapRecord` contains:

- bounded `unexplained_residual_score`;
- conflicting, eligible-evidence, accepted-candidate, and rejected-candidate
  counts;
- uncovered criterion refs;
- explanation limitations;
- deterministic concise reason;
- metric/policy versions and metadata.

It must be structured and cannot be prose-only. It is present when a known
divergence retains material unexplained residual or unresolved candidate
conflict. It is separate from missing measurement.

## Root Cause Candidate

Use conceptual `RootCauseCandidate` with stable identity, category, subject,
description, role, disposition, confidence, temporal precedence, direct
relevance, evidence coverage, independent support count, supporting and
contradicting evidence refs, parent/child candidate IDs, limitations,
alternatives, rejection reason, policy version, and metadata.

Use `RootCauseCategory`:

- `FACTOR_WEAKENING`
- `FACTOR_DISAPPEARANCE`
- `FACTOR_NON_CONFIRMATION`
- `FACTOR_CONTRADICTION`
- `STAGE_REGRESSION`
- `STAGE_STAGNATION`
- `MATURITY_WITHOUT_CONFIRMATION`
- `AVAILABILITY_DEGRADATION`
- `OBSERVABILITY_LIMITATION`
- `INTELLIGENCE_LIMITATION`
- `UNKNOWN`

Use `RootCauseRole`: `PRIMARY_CANDIDATE`, `CONTRIBUTING_CANDIDATE`,
`CONTEXT_CANDIDATE`, `ALTERNATIVE_CANDIDATE`, `REJECTED_CANDIDATE`.

Use `RootCauseDisposition`: `ACCEPTED`, `PARTIALLY_SUPPORTED`, `REJECTED`,
`UNRESOLVED`.

Candidate confidence means explanation support only. Accepted market or
intelligence candidates require temporal precedence; equal timestamps are
ambiguous and cannot satisfy strict precedence. Unavailable input can support
an observability candidate but cannot be a measured market cause. Rejected and
unresolved candidates remain auditable.

## Root Cause Tree

Use `RootCauseTree` as an immutable directed explanatory graph with explicit
tree ID/version, ordered candidate IDs, ordered root IDs, and edges represented
by parent/child candidate identities.

Invariants:

1. one or more accepted/partially supported roots are allowed; an empty tree is
   valid only when no supported explanation exists;
2. all referenced candidate IDs exist exactly once;
3. cycles and self-links are forbidden;
4. a candidate has at most one accepted-tree parent in Phase 1;
5. parent/child declarations must be reciprocal and deterministic;
6. rejected candidates remain outside the accepted tree but inside the trace;
7. alternative/unresolved candidates are preserved without forced collapse;
8. maximum depth is policy controlled; Phase 1 default proposal is 4;
9. parent-child means explanatory dependency, not proven causal direction;
10. canonical order is role precedence, category, subject, then candidate ID.

Canonical example:

```text
Primary: Momentum deterioration
└── Contributing: Weak volume confirmation
    └── Context: Funding remained unavailable

Alternative: Structure weakening
Rejected: Whale activity — source input remained MISSING, not measured evidence
```

## Evidence reference contract

`RealityGapEvidenceReference` stores references only: evidence ID/type,
artifact identity, Timeline/version/entry, UTC observation time, factor name,
measured value, availability, delta state/prior/new values, criterion reference,
relation, normalized evidence quality, eligibility, rejection reason, and
primitive metadata.

Use `RealityGapEvidenceType`:

- `EXPECTATION_BASIS`
- `EVALUATION_FACT`
- `TIMELINE_ENTRY`
- `SITUATION_DNA`
- `DNA_DELTA`
- `STAGE_CHANGE`
- `AVAILABILITY_CHANGE`
- `IDENTITY_TRACE`
- `EVOLUTION_TRACE`
- `OBSERVABILITY_FACT`

Use `RealityGapEvidenceRelation`: `SUPPORTS`, `CONTRADICTS`, `PRECEDES`,
`FOLLOWS`, `EXPLAINS`, `LIMITS_EXPLANATION`, `ALTERNATIVE_TO`, `UNRELATED`.

None and measured zero remain distinct. Every measured value carries
availability. Evidence later than `evaluated_at` or `window_end` is ineligible;
it may appear only in the rejected-evidence trace with an explicit time-boundary
reason. Provider payloads, credentials, private headers, and mutable artifacts
are prohibited. Duplicate reference IDs and duplicate semantic references are
rejected. Ordering is deterministic by observed time, type, artifact ID,
criterion reference, then evidence ID.

## Reality Gap Analysis contract

`RealityGapAnalysis` is immutable and contains:

- exact gap/expectation/evaluation/Timeline identity, uppercase asset,
  analysis version, UTC creation/evaluation timestamps;
- primary type, composable dimensions, intelligence/observability gap records,
  explanation gap, and severity;
- source Surprise Score, Knowledge Gap, Explanation Confidence, unexplained
  residual, and their structured inputs/versions;
- missing, unexpected, contradictory, and fulfilled event refs;
- all candidates, accepted/rejected/unresolved IDs, Root Cause Tree, supporting
  evidence, and limitations;
- immutable source expectation/evaluation snapshots, Timeline versions, source
  entry IDs, policy/taxonomy/metric/trace versions, and metadata;
- immutable `RealityGapDecisionTrace`.

It has no direction, trade, execution, profitability, outcome reinterpretation,
learning, or cumulative Intelligence Debt field. Serialization is primitive,
deterministic, UTC-preserving, and round-trippable.

## Metric decision

Option A (optional/uncomputed metrics) avoids premature precision but leaves the
first analysis contract unable to answer two explicit domain questions and
makes later outputs harder to compare.

Option B (conservative deterministic formulas) is accepted because every input
is structured, immutable, bounded, traceable, and non-causal. Formulas are
policy, not learned truth. They are implemented only in future Step 7E after
contract/candidate/evidence phases pass review.

Metric policy version is independent and begins conceptually at `"1"`.

### Component normalization

All components are 0..100 and preserved in `RealityGapMetricInputs`:

- `eligible_evidence_coverage`: eligible measured references / expected
  evidence denominator; denominator and counts are stored;
- `temporal_order_quality`: average accepted candidate precedence score
  (`PRECEDES=100`, explicit equal-time ambiguity `=50`, non-preceding `=0`);
- `direct_criterion_relevance`: average accepted candidate direct-relevance
  score;
- `independent_support`: per-candidate mapping of independent supports
  (`0=0`, `1=50`, `2=75`, `3+=100`), averaged across accepted candidates;
- `observability_quality = 0.70 * eligible_evidence_coverage + 0.30 *
  mean_eligible_measured_quality`; eligible measured evidence requires a stored
  0..100 quality under metric version 1;
- `candidate_conflict = 100 * conflicting_candidate_pair_count /
  possible_candidate_pair_count`; pairs are unique unordered pairs among
  accepted/partially supported candidates, and the score is 0 when fewer than
  two such candidates exist;
- `observability_deficit = 100 - observability_quality`;
- `confidence_deficit = 100 - explanation_confidence`.

No accepted candidate means temporal, relevance, and independent-support
components are 0.

All public metric ratios and components use the 0..100 scale. Counts and
denominators remain stored so no scale or fallback is inferred.

### Unexplained residual

Do not sum candidate confidences. For each divergence criterion, take the
maximum non-overlapping support assigned by an accepted candidate:

- directly supported and temporally preceding: `1.0`;
- partially supported or equal-time ambiguous: `0.5`;
- unresolved/rejected/uncovered: `0.0`.

Each criterion is counted once regardless of candidate overlap. With `N`
divergence criteria:

```text
unexplained_residual = 100 * (1 - sum(criterion_support) / N)
```

If `N=0`, residual is `0` for `NO_GAP`; otherwise classification is invalid.
Observability limitations are not added to residual because they enter
Knowledge Gap separately. Inputs and per-criterion assignments are traced.

### Explanation Confidence

```text
base =
    0.30 * eligible_evidence_coverage
  + 0.25 * temporal_order_quality
  + 0.25 * direct_criterion_relevance
  + 0.15 * independent_support
  + 0.05 * observability_quality

explanation_confidence = clamp(base - 0.40 * candidate_conflict, 0, 100)
```

Conflict can subtract at most 40 points. Confidence is explanation support, not
causal probability or market/trade confidence.

### Knowledge Gap

```text
knowledge_gap = clamp(
    0.40 * unexplained_residual
  + 0.25 * observability_deficit
  + 0.20 * candidate_conflict
  + 0.15 * confidence_deficit,
  0,
  100
)
```

The metrics are related but not inverses. Surprise is excluded from both
quality formulas; it may inform severity. Every component, denominator,
rounding rule, and metric version must be stored. Phase 1 rounding is six
decimal places after final clamping. Booleans/non-finite values are invalid.

## Severity policy

Use `RealityGapSeverity`: `NONE`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.

Severity is deterministic policy version `"1"` and represents importance to
system understanding only:

- `NONE`: primary `NO_GAP`, no material secondary dimension, Surprise <= 20.
- `LOW`: non-stage divergence with Surprise < 40, Knowledge Gap < 40, and at
  most one material event.
- `MEDIUM`: Surprise 40..69, Knowledge Gap 40..69, multiple non-stage events,
  or a bounded observability limitation affecting one criterion.
- `HIGH`: Surprise >= 70, Knowledge Gap >= 70, stage-level divergence, a
  supported Intelligence Gap, or multiple core criteria affected; sufficient
  observability is not required.
- `CRITICAL`: all are required: HIGH expectation strength; primary
  `CONTRADICTORY_REALITY` or `MIXED_GAP`; stage-level impact; Knowledge Gap >= 70
  or a supported non-UNKNOWN Intelligence Gap; and observability quality >= 60
  proving the divergence is real.

An Observability Gap alone is capped at `HIGH`; it is `HIGH` only when it
disables a core capability across the entire evaluation. Otherwise it is
`MEDIUM` or lower. Severity rules use explicit precedence `CRITICAL`, `HIGH`,
`MEDIUM`, `LOW`, `NONE`, and every triggered condition is traced. Recurrence is
not available in one-record severity.

## Decision trace

`RealityGapDecisionTrace` is immutable and stores trace identity/version,
formal evaluation status/gap type, eligible window, considered/rejected evidence,
dimensions/types considered, ordered classification steps, candidate generation,
acceptance/rejection steps, metric inputs/outputs, severity inputs/output,
unresolved questions, policy versions, UTC creation time, and primitive
metadata.

The trace contains structured decision facts and concise reasons. It contains
no hidden LLM reasoning, private chain of thought, provider secrets, or prose as
authority. Every output field is traceable to exact inputs and policy.

## Intelligence Debt boundary

Intelligence Debt is a future aggregate across many immutable analyses. One
analysis may emit a stable `intelligence_debt_event_ref` or qualifying
Intelligence Gap record for future aggregation, but it cannot own or update a
cumulative debt score.

Future memory/learning analytics may aggregate recurring detection,
interpretation, correlation, expectation-formation, calibration, and policy
coverage gaps. Historical analyses remain unchanged. Debt priority may guide
engineering review but cannot directly alter trading behavior.

## Versioning and identity

- `gap_id` identifies one conceptual analysis lineage for fixed expectation ID,
  evaluation ID, Timeline ID, and evidence boundary.
- `analysis_version` identifies immutable revisions starting at 1.
- expectation/evaluation identities and original evidence boundary never change
  within a lineage.
- re-analysis cannot admit later/out-of-window evidence.
- a new version may correct an engine defect or apply a newly approved policy,
  metric, taxonomy, or trace version while preserving every prior record.
- `analysis_policy_version`, `metric_version`, `taxonomy_version`,
  `root_cause_tree_version`, and `trace_version` are independent strings and
  always stored.
- legitimate version differences include classification, candidates, tree,
  metrics, severity, and trace produced by an explicitly different approved
  policy over the same immutable source boundary.
- source snapshots and eligible evidence set may not differ silently.
- deterministic `gap_id`/version ID generation remains Step 7C orchestrator
  responsibility; the contract requires stable, non-empty IDs and lineage
  consistency rather than prescribing a hash prematurely.

## Anti-hindsight invariants

1. Only original expectation/evaluation eligible evidence is used.
2. Outcome facts and future provider data are excluded.
3. Current defaults never replace stored policy/contract metadata.
4. Prior analyses are immutable and never overwritten.
5. Rendered prose is not parsed as evidence.
6. No candidate is a definitive causal fact.
7. Missing data remains an observability fact.
8. Similar historical patterns are excluded.
9. Learning can consume records only after creation and cannot mutate them.
10. New analysis versions cannot widen the historical evidence boundary.

## Alternatives considered

### A. One exclusive gap enum

Rejected because market, intelligence, observability, and explanation gaps can
coexist and an exclusive enum destroys information.

### B. Free-form LLM explanation

Rejected because it is not deterministic structured evidence and may fabricate
causal claims. LLM rendering may later summarize records only.

### C. One definitive root cause

Rejected because evidence supports plausible candidates, dependencies, and
alternatives rather than causal certainty.

### D. Flat cause list

Rejected because it cannot represent explanatory dependency, alternatives,
roots, or overlap while preserving deterministic structure.

### E. Composable dimensions plus structured candidate tree

Accepted. It preserves orthogonal gaps, evidence provenance, candidate
disposition, alternatives, dependencies, auditability, and future aggregation.

## Trade-offs

Positive consequences: explicit uncertainty, no silent data loss, transparent
metrics, deterministic auditing, stable learning inputs, and strict separation
from production decisions. Negative consequences: larger contracts, more
validation/versioning, conservative unresolved results, metric policy maintenance,
and substantial golden-test requirements before runtime use.

## Future phases

- **Step 7C:** immutable enums/contracts, validation, deep freezing,
  serialization, IDs/version lineage, no analysis engine.
- **Step 7D:** window-bounded evidence extraction and deterministic candidate
  generation/disposition, no metrics or classification authority.
- **Step 7E:** composable classification, tree validation/construction, metric
  formulas, severity, and full trace.
- **Step 7F:** process-local orchestration with Expectation Evaluator and
  Timeline Evolution.

Persistence, Telegram, learning, Outcome Analysis, providers, production, and
deployment require separate later approval.
