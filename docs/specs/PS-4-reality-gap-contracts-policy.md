# PS-4 Step 7B — Reality Gap Contracts and Policy Specification

## Objective

Define implementation-ready conceptual contracts and deterministic policies for
future Reality Gap runtime phases without adding Python runtime code or changing
Expectation, Evaluation, Timeline, Identity, or Evolution contracts.

## Scope and exclusions

Scope: enums, immutable record domains, evidence references, composable gap
dimensions, candidate taxonomy/disposition, explanatory tree, metrics, severity,
decision trace, serialization, versioning, Intelligence Debt boundary, future
acceptance criteria, and unresolved implementation details.

Excluded: runtime code, provider calls, persistence, learning, Outcome Analysis,
Telegram, production decisions, deployment, Hostinger, and contract integration.

## Conceptual enums

### RealityGapDimension

`MARKET`, `INTELLIGENCE`, `OBSERVABILITY`, `EXPLANATION`, `UNKNOWN`.

Dimensions are ordered, unique, composable, and evidence-backed. `UNKNOWN` is
exclusive of specific dimensions.

### RealityGapPrimaryType

`NO_GAP`, `MISSING_EXPECTED_REALITY`, `UNEXPECTED_REALITY`,
`CONTRADICTORY_REALITY`, `MIXED_GAP`, `OBSERVABILITY_GAP`,
`EXPLANATION_GAP`, `UNKNOWN`.

Primary type describes the dominant observed divergence and does not suppress
secondary dimensions.

### IntelligenceGapType

- `DETECTION_GAP`
- `INTERPRETATION_GAP`
- `CORRELATION_GAP`
- `EXPECTATION_FORMATION_GAP`
- `CONFIDENCE_CALIBRATION_GAP`
- `POLICY_COVERAGE_GAP`
- `UNKNOWN`

### ObservabilityGapType

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

### RootCauseCategory

`FACTOR_WEAKENING`, `FACTOR_DISAPPEARANCE`, `FACTOR_NON_CONFIRMATION`,
`FACTOR_CONTRADICTION`, `STAGE_REGRESSION`, `STAGE_STAGNATION`,
`MATURITY_WITHOUT_CONFIRMATION`, `AVAILABILITY_DEGRADATION`,
`OBSERVABILITY_LIMITATION`, `INTELLIGENCE_LIMITATION`, `UNKNOWN`.

### RootCauseRole

`PRIMARY_CANDIDATE`, `CONTRIBUTING_CANDIDATE`, `CONTEXT_CANDIDATE`,
`ALTERNATIVE_CANDIDATE`, `REJECTED_CANDIDATE`.

### RootCauseDisposition

`ACCEPTED`, `PARTIALLY_SUPPORTED`, `REJECTED`, `UNRESOLVED`.

### TemporalPrecedence

`PRECEDES`, `EQUAL_TIME_AMBIGUOUS`, `FOLLOWS`, `UNKNOWN`.

Accepted market/intelligence candidates require `PRECEDES`. Equal timestamps
may support context or partial support but not strict causal precedence.

### RealityGapEvidenceType

`EXPECTATION_BASIS`, `EVALUATION_FACT`, `TIMELINE_ENTRY`, `SITUATION_DNA`,
`DNA_DELTA`, `STAGE_CHANGE`, `AVAILABILITY_CHANGE`, `IDENTITY_TRACE`,
`EVOLUTION_TRACE`, `OBSERVABILITY_FACT`.

### RealityGapEvidenceRelation

`SUPPORTS`, `CONTRADICTS`, `PRECEDES`, `FOLLOWS`, `EXPLAINS`,
`LIMITS_EXPLANATION`, `ALTERNATIVE_TO`, `UNRELATED`.

### EvidenceEligibility

`ELIGIBLE`, `AFTER_EVALUATED_AT`, `AFTER_WINDOW_END`, `BEFORE_SOURCE`,
`IDENTITY_MISMATCH`, `UNSTRUCTURED`, `DUPLICATE`, `UNKNOWN`.

Only `ELIGIBLE` evidence may affect classification, candidates, metrics, or
severity. Rejected evidence remains in the decision trace.

### RealityGapSeverity

`NONE`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.

Severity concerns system understanding only and carries no trading meaning.

## Conceptual model: RealityGapEvidenceReference

Fields and semantics:

- `evidence_id`: stable required identity;
- `evidence_type`: one `RealityGapEvidenceType`;
- `artifact_id`: stable source artifact reference, not embedded artifact;
- `timeline_id`, `timeline_version`, `entry_id`: lineage reference where
  applicable;
- `observed_at`: timezone-aware UTC evidence timestamp;
- `factor_name`: normalized optional factor identity;
- `measured_value`: optional measured 0..100 value; measured zero is valid;
- `availability`: exact source availability state;
- `quality`: optional 0..100 evidence quality; required for eligible measured
  evidence used by metric policy version 1;
- `delta_state`, `prior_value`, `new_value`: structured change provenance;
- `criterion_reference`: stable affected expectation/evaluation criterion;
- `relation`: one `RealityGapEvidenceRelation`;
- `eligibility`: one `EvidenceEligibility`;
- `rejection_reason`: required for non-eligible evidence;
- `metadata`: deeply immutable primitive mapping.

Invariants:

1. IDs and UTC timestamp are required.
2. Timeline versions, when present, are integers >= 1 and booleans are invalid.
3. AVAILABLE measured factor evidence requires a value; non-AVAILABLE factor
   evidence cannot carry a hidden measured value.
4. `None` and measured zero are distinct.
5. Prior/new values obey their corresponding availability/delta semantics.
6. Evidence after `evaluated_at` or `window_end` is ineligible.
7. Provider payloads, credentials, headers, mutable objects, and prose-only
   claims are forbidden.
8. Evidence ID and semantic tuple `(type, artifact, entry, criterion, relation)`
   are unique inside an analysis.
9. Canonical order is `(observed_at, evidence_type, artifact_id,
   criterion_reference, evidence_id)`.

## Conceptual model: IntelligenceGapRecord

Fields:

- stable record ID and `IntelligenceGapType`;
- affected rule/criterion and source reasoning artifact;
- omitted, misinterpreted, or uncorrelated evidence refs;
- source policy/rule/taxonomy versions;
- bounded classification confidence;
- concise structured reason, limitations, and metadata.

An intelligence record requires at least one eligible evidence reference to a
system representation/reasoning mismatch. Wrong outcome alone is invalid.
`UNKNOWN` requires evidence of a limitation plus explicit inability to subtype.

## Conceptual model: ObservabilityGapRecord

Fields:

- stable record ID and `ObservabilityGapType`;
- expected source and factor reference;
- actual availability state;
- evidence window and relevant timestamps;
- eligible denominator, measured count, measured ratio;
- quality score when available;
- affected criterion refs;
- evidence refs, limitations, reason, and metadata.

Denominator/counts are non-negative integers; all public ratios use the 0..100
scale. `UNSUPPORTED_FACTOR` and `PROVIDER_ERROR` remain distinct.
The record never claims an unobserved market value.

## Conceptual model: ExplanationGapRecord

Fields:

- `unexplained_residual_score` 0..100;
- conflicting candidate count;
- eligible evidence count;
- accepted, partially supported, rejected, and unresolved candidate counts;
- uncovered criterion refs;
- explanation limitations;
- deterministic reason;
- metric/policy versions and metadata.

Counts are non-negative integers. Uncovered criteria must belong to the formal
divergence set. A prose reason without structured residual/candidate/evidence
facts is invalid.

## Conceptual model: RootCauseCandidate

Fields:

- `candidate_id`, category, subject, concise description;
- role and disposition;
- explanation-support confidence 0..100;
- temporal precedence;
- direct relevance 0..100;
- evidence coverage 0..100;
- independent support count;
- ordered unique supporting/contradicting evidence IDs;
- optional parent candidate ID and ordered child IDs;
- ordered limitations and alternative candidate IDs;
- rejection reason;
- policy version and metadata.

Invariants:

1. Never label a candidate as proven or causal fact.
2. `ACCEPTED` market/intelligence candidates require `PRECEDES`, at least one
   supporting eligible evidence ref, direct relevance > 0, and non-rejected
   role.
3. `PARTIALLY_SUPPORTED` permits equal-time ambiguity or limited relevance but
   requires evidence and explicit limitation.
4. `REJECTED` requires rejection role or explicit rejection reason and remains
   traceable.
5. `UNRESOLVED` requires a limitation/conflict reason.
6. Unavailable facts can support observability/context candidates only.
7. Supporting and contradicting refs are disjoint.
8. Alternative IDs and child IDs are unique and cannot self-reference.
9. Confidence is explanation support, not causal probability.

## Conceptual model: RootCauseTree

Fields:

- `tree_id`, `tree_version`;
- ordered root candidate IDs;
- ordered included candidate IDs;
- maximum allowed depth;
- policy version and metadata.

Validation:

- every ID resolves to one candidate in the owning analysis;
- candidate IDs are unique;
- cycles and self-links are forbidden;
- accepted-tree parent/child links are reciprocal;
- Phase 1 candidate has at most one accepted-tree parent;
- roots have no accepted-tree parent;
- rejected candidates are excluded from included/root IDs;
- alternatives/unresolved candidates remain in analysis/trace;
- empty roots/included IDs are permitted only with no accepted or partially
  supported candidates;
- actual depth cannot exceed policy maximum (proposed default 4);
- canonical traversal uses root order then deterministic child order by role,
  category, subject, ID.

Parent-child denotes explanatory dependency, not proven causal direction.

## Conceptual model: RealityGapMetricInputs

Fields:

- eligible evidence expected/measured counts and coverage;
- temporal-order component;
- direct-relevance component;
- independent-support component;
- observability-quality/deficit components;
- candidate-conflict component and conflict facts;
- divergence criterion count and per-criterion support assignments;
- unexplained residual;
- explanation-confidence deficit;
- formula/rounding version and metadata.

Every component is 0..100, finite, non-boolean, and derivable from referenced
structured facts. Counts and denominators are preserved.

## Metric policy version 1

Step 7B selects conservative computed metrics (Option B) for future Step 7E.
Step 7C contracts should allow metrics to remain absent until the calculation
phase, but a completed analysis under metric version 1 must contain both scores
and all inputs.

### Unexplained residual

Build the divergence criterion set from formal missing, unexpected, and
contradictory criterion/event refs. For each unique criterion assign maximum
non-overlapping accepted support:

- 1.0: directly relevant, eligible, temporally preceding accepted candidate;
- 0.5: partially supported or equal-time ambiguous candidate;
- 0.0: unresolved, rejected, or uncovered.

```text
residual = clamp(100 * (1 - sum(support_i) / criterion_count), 0, 100)
```

Each criterion contributes once. Candidate confidence is not summed. For
`NO_GAP` with zero divergence criteria residual is 0; any other zero-criterion
classification is invalid.

### Component policies

- evidence coverage = `100 * measured_eligible / expected_eligible`; zero
  denominator requires an observability error and component 0;
- temporal quality: `PRECEDES=100`, `EQUAL_TIME_AMBIGUOUS=50`, other/unknown=0,
  averaged across accepted/partially supported candidates;
- direct relevance: average candidate relevance;
- independent support per candidate: 0 refs=0, 1=50, 2=75, 3+=100; then average;
- mean eligible measured quality: arithmetic mean of stored 0..100 quality for
  eligible measured evidence; missing required quality makes metric calculation
  invalid rather than invoking a fallback;
- observability quality = `0.70*eligible_evidence_coverage +
  0.30*mean_eligible_measured_quality`;
- conflict: let `n` be accepted/partially supported candidate count, possible
  unique unordered pairs `P=n*(n-1)/2`, and `C` be traced mutually
  contradicting pairs; `conflict=100*C/P` when `P>0`, otherwise 0. Each pair is
  counted once and must reference structured contradicting evidence.

### Explanation Confidence

```text
base = 0.30*coverage
     + 0.25*temporal_quality
     + 0.25*direct_relevance
     + 0.15*independent_support
     + 0.05*observability_quality

explanation_confidence = clamp(base - 0.40*conflict, 0, 100)
```

No accepted/partially supported candidate means temporal, relevance, and
independent-support components are 0. The score is explanation support only.

### Knowledge Gap

```text
knowledge_gap = clamp(
    0.40*unexplained_residual
  + 0.25*(100-observability_quality)
  + 0.20*conflict
  + 0.15*(100-explanation_confidence),
  0,
  100
)
```

Surprise is intentionally absent. Metrics are related but not inverses. Final
values are clamped and rounded to six decimal places. Intermediate components
are calculated without early rounding. Formula and component-policy versions
are preserved independently if needed.

## Conceptual model: RealityGapSeverityInputs

Fields:

- formal evaluation status/gap type;
- expectation strength;
- Surprise Score;
- primary type/dimensions;
- stage-impact boolean and evidence refs;
- missing/unexpected/contradictory event counts;
- Knowledge Gap;
- Intelligence Gap records and confidence;
- observability quality and core-capability impact;
- triggered severity rules and policy version.

## Severity policy version 1

Rules are evaluated from most severe to least:

1. `CRITICAL` only when all hold: expectation strength HIGH; primary type is
   contradictory or mixed; measured stage-level impact; Knowledge Gap >= 70 or
   at least one supported non-UNKNOWN Intelligence Gap; observability quality
   >= 60.
2. `HIGH` when any hold: Surprise >= 70; Knowledge Gap >= 70; measured stage
   divergence; supported Intelligence Gap; multiple core criteria affected; or
   an observability failure disables a core capability across the whole window.
3. `MEDIUM` when any hold: Surprise 40..69; Knowledge Gap 40..69; multiple
   non-stage events; or bounded observability limitation affects one criterion.
4. `LOW` for a remaining material non-stage divergence with Surprise < 40,
   Knowledge Gap < 40, and at most one material event.
5. `NONE` requires primary NO_GAP, no material secondary dimension, and
   Surprise <= 20.

An Observability Gap alone cannot be `CRITICAL`. A core-capability-wide
observability failure may be `HIGH`; otherwise observability alone is capped at
`MEDIUM`. Every matched and skipped rule is preserved in the trace. Values at
numeric boundaries belong to the more severe inclusive band stated above.

## Conceptual model: RealityGapDecisionTrace

Fields:

- trace ID/version and UTC creation time;
- expectation status and evaluation gap type;
- exact eligible window/cutoff;
- considered and rejected evidence IDs/reasons;
- gap dimensions/types considered;
- ordered classification steps;
- candidate generation, acceptance, partial-support, rejection, and unresolved
  steps;
- metric inputs/outputs/formula versions;
- severity inputs/output/policy version;
- unresolved questions;
- all policy/taxonomy/tree/contract versions;
- primitive metadata.

Invariants:

- every final type, dimension, candidate disposition, metric, and severity maps
  to one or more trace steps;
- ordering is deterministic and duplicate step IDs are rejected;
- rejected evidence/candidates are retained;
- structured facts and concise reasons only;
- no hidden LLM reasoning or private chain of thought;
- no provider secrets or mutable artifacts;
- prose rendering is not authoritative.

## Conceptual model: RealityGapAnalysis

### Identity and time

`gap_id`, `expectation_id`, `evaluation_id`, `timeline_id`, uppercase asset,
analysis version >= 1, UTC `created_at` and `evaluated_at`.

### Classification

One primary type; ordered dimensions; ordered Intelligence/Observability Gap
records; optional structured Explanation Gap; severity.

### Metrics

Source Surprise Score, optional Knowledge Gap/Explanation Confidence during
contract-only phases, unexplained residual, immutable metric inputs, metric
version. A completed Step 7E analysis requires all metrics.

### Reality and explanation

Ordered unique missing, unexpected, contradictory, and fulfilled event refs;
ordered candidates; validated tree; accepted/rejected/unresolved candidate IDs;
supporting evidence references; limitations.

### Provenance and trace

Deeply immutable expectation/evaluation snapshots, Timeline versions, source
entry IDs, analysis/taxonomy/metric/tree/trace versions, decision trace, and
primitive metadata.

### Analysis invariants

1. Exact IDs are non-empty and mutually consistent.
2. Source snapshots match IDs and original evidence boundary.
3. Analysis/evidence Timeline versions are >= 1 and belong to the same lineage.
4. Inputs and previous records are never mutated.
5. Primary type/dimensions satisfy their mapping policy.
6. All event/candidate/evidence/tree/trace references resolve.
7. Candidate disposition ID groups are disjoint and exhaustive.
8. Metrics match stored inputs and versions when present.
9. Prior analysis versions remain immutable.
10. No direction, trade, execution, profit, learning, cumulative debt, or
    outcome reinterpretation fields.

## Primary type and dimension baseline mapping

- fulfilled, no unexpected, no unresolved explanation: `NO_GAP` with an empty
  dimensions tuple;
- fulfilled plus unexpected: `UNEXPECTED_REALITY` + `MARKET`;
- missing: `MISSING_EXPECTED_REALITY` + `MARKET`;
- contradicted: `CONTRADICTORY_REALITY` + `MARKET`;
- multiple formal market types: `MIXED_GAP` + `MARKET`;
- expired for data limitations: `OBSERVABILITY_GAP` + `OBSERVABILITY`;
- indeterminate with simultaneous formal fulfillment/contradiction evidence:
  `MIXED_GAP` plus `MARKET` and `EXPLANATION`; indeterminate caused only by
  unusable contract/insufficient classification evidence: `UNKNOWN` plus
  `EXPLANATION`, and `OBSERVABILITY` when measurement limitations are present;
- structured intelligence limitation adds `INTELLIGENCE` without replacing the
  market primary;
- known divergence with material unexplained residual adds `EXPLANATION`;
- insufficient classification evidence permits `UNKNOWN`.

These mappings are canonical for taxonomy policy version 1.

## Versioning and lineage

- `gap_id` identifies fixed expectation/evaluation/Timeline/evidence-boundary
  lineage.
- `analysis_version` starts at 1 and increments for immutable revisions.
- old versions are never overwritten or deleted by analysis logic.
- later/out-of-window evidence cannot create a legitimate new version.
- defect correction or newly approved policy/taxonomy/metric/trace version may
  create a new version using the same immutable source boundary.
- `analysis_policy_version`, `metric_version`, `taxonomy_version`,
  `tree_version`, and `trace_version` are independent required provenance.
- deterministic ID algorithm belongs to Step 7C orchestrator design; this spec
  requires stable IDs, lineage consistency, and collision/duplicate rejection.

## Serialization expectations

Future contracts must use Python 3.9-compatible frozen dataclasses and standard
library only unless separately approved. Public values serialize as primitive
dict/list/string/number/boolean/null values. Enums serialize by public value;
UTC timestamps serialize ISO-8601; tuples serialize lists and restore ordered
tuples; mappings deep-freeze and serialize with deterministic key order.
Non-finite numbers, booleans as numerics, callables, mutable artifact objects,
provider payloads, secrets, and private headers are rejected. Full round-trip
must preserve values, order, identity, versions, and timestamp meaning.

## Anti-hindsight requirements

1. Only original window/evaluation-eligible evidence.
2. No Outcome facts or future provider data.
3. No current-default substitution.
4. No prior-analysis rewrite.
5. No prose parsing as evidence.
6. No definitive causality claims.
7. Missing data remains observability, never hidden market value.
8. Similar historical patterns are excluded.
9. Learning consumes only after immutable creation.
10. New versions cannot widen evidence boundaries.

## Intelligence Debt boundary

One analysis may expose immutable Intelligence Gap records or a stable debt-event
reference. It cannot calculate, store, or mutate long-term Intelligence Debt.
Debt is a future aggregation over many records in memory/learning analytics.
Its priority may guide engineering review only and cannot modify production
trading behavior or historical analyses.

## Future acceptance criteria

### Step 7C — Contracts only

- all enums and immutable models implemented with exact public semantics;
- deep immutability, validation, serialization, deterministic ordering, and UTC;
- lineage/version and reference resolution validation;
- tree acyclicity/depth/parent rules;
- optional metrics permitted but no calculator;
- no engine/provider/persistence/Telegram/production/learning/outcome imports;
- existing regressions remain green.

### Step 7D — Evidence and candidates

- exact time/identity eligibility filtering;
- stable evidence refs without mutable embedding;
- deterministic candidate taxonomy, roles, dispositions, alternatives, and
  rejections for all seven Expectation rule families;
- no classification/metric/severity authority;
- no causal claims or prose parsing.

### Step 7E — Analysis policy

- canonical primary/dimension precedence finalized;
- tree construction and validation;
- component extraction, conflict normalization, formulas, six-place rounding;
- severity decision table and complete structured trace;
- golden boundary, monotonicity, overlap, missing-data, and anti-hindsight tests.

### Step 7F — Process-local orchestration

- integration only with immutable Expectation Evaluation and Timeline Evolution;
- no persistence, Telegram, production decisions, providers, learning, outcome,
  or deployment without separate approval.

## Unresolved implementation details

1. Stable criterion-reference naming across all seven Expectation rules.
2. Deterministic gap/candidate/evidence/trace ID algorithm.
3. Taxonomy and policy version string format beyond initial `"1"`.
4. Maximum collection sizes and tree depth enforcement constants.
5. Exact evidence independence/dependency representation.
6. How new analysis versions declare defect-correction versus policy-upgrade
    reason without implying historical mutation.
