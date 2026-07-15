# PS-4 Step 7A — Reality Gap Engine Architecture Specification

## Objective

Specify the future boundary that explains differences between an immutable
Situation Expectation and the measured reality recorded by its immutable
Evaluation and window-bounded Timeline evidence.

This specification defines concepts and acceptance criteria only. It does not
approve Python contracts, scoring formulas, persistence, or integration.

## Scope

- Reality Gap versus Expectation Evaluation responsibility;
- conceptual inputs and output;
- gap and severity categories;
- Root Cause Candidate semantics;
- Knowledge Gap and Explanation Confidence definitions;
- evidence, availability, temporal, and anti-hindsight rules;
- deterministic decision-trace requirements;
- learning and outcome boundaries;
- future implementation acceptance criteria;
- unresolved policy questions.

## Out of scope

- Python models or engine;
- exact numeric formulas or calibrated thresholds;
- expectation/evaluation/Timeline contract changes;
- persistence, database, repository, or cache;
- Telegram or other UI;
- production decisions or pipeline integration;
- learning or policy optimization;
- outcome analysis or pattern similarity;
- LLM causal explanation;
- providers, networking, deployment, or Hostinger.

## Responsibility boundary

Expectation Evaluation formally classifies what happened relative to the stored
rule contract. Reality Gap Analysis explains why a classified divergence may
have occurred and how much of it remains unexplained.

The future engine must not:

- alter Evaluation status, gap type, Surprise Score, or observed facts;
- reinterpret the expectation with current defaults;
- assert causal truth from correlation;
- fetch new evidence;
- use post-window outcomes;
- create trade recommendations;
- learn from or mutate its own outputs.

## Conceptual inputs

### Required

1. Immutable `SituationExpectation`, including source snapshot, stored
   `evaluation_contract`, window, identity, and version.
2. Immutable `SituationExpectationEvaluation`, including status, evaluation gap
   type, Surprise Score, evidence cutoff, evaluated entry IDs, source snapshot,
   and policy/contract provenance.
3. Exact immutable Timeline entries referenced by the evaluation and eligible
   DNA deltas inside the expectation window.

### Optional when already preserved

- identity trace that established situation continuity;
- evolution decisions and DNA delta trace for eligible Timeline versions;
- structured evidence references and availability provenance.

Optional input absence must reduce observability or explanation confidence; it
must not be synthesized from current state.

## Conceptual output: RealityGapAnalysis

A future immutable record is expected to represent these domains without yet
fixing Python field types:

- identity: gap, expectation, evaluation, Timeline, asset, creation time;
- provenance: source snapshots, source Timeline versions, evidence window,
  evaluated entry IDs, policy/contract versions;
- classification: primary gap type, optional secondary dimensions, severity;
- metrics: Knowledge Gap Score and Explanation Confidence;
- events: missing expected, unexpected, and contradictory events;
- explanation: root-cause candidates, supporting evidence, rejected
  explanations, limitations, alternatives, unexplained residual;
- audit: ordered deterministic decision trace and metadata.

The record must be immutable, serializable, UTC-aware, deterministic, and free
of trade/outcome/learning fields. Later analyses must be new versioned records,
not mutations.

## Conceptual categories

### RealityGapType

- `NO_GAP`
- `MISSING_EXPECTED_REALITY`
- `UNEXPECTED_REALITY`
- `CONTRADICTORY_REALITY`
- `MIXED_GAP`
- `OBSERVABILITY_GAP`
- `EXPLANATION_GAP`
- `UNKNOWN`

Primary classification must be deterministic. The future contract should also
preserve orthogonal observability and explanation dimensions so one primary
type does not erase another.

### RealityGapSeverity

- `NONE`
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Severity describes impact on the system's understanding, not market direction,
trade risk, financial loss, volatility, execution urgency, or liquidation risk.

### RootCauseCategory

Candidate categories for policy review include:

- `WEAK_VOLUME_CONFIRMATION`
- `MOMENTUM_DETERIORATION`
- `STRUCTURE_WEAKENING`
- `FACTOR_BECAME_UNAVAILABLE`
- `STAGE_REGRESSION`
- `MATURITY_WITHOUT_CONFIRMATION`
- `INITIATING_FACTOR_DISAPPEARED`
- `INSUFFICIENT_DATA_COVERAGE`
- `CONFLICTING_EVIDENCE`
- `UNEXPLAINED`

The exact enum is not approved until Step 7B verifies it against all seven
Expectation rule families.

## Root Cause Candidate conceptual model

Each candidate must preserve:

- stable candidate identity and category;
- criterion or unexpected event it may explain;
- measured evidence references and timestamps;
- temporal precedence result;
- relevance and independence assessment;
- bounded confidence if a reviewed formula exists;
- limitations and unavailable dependencies;
- conflicting and alternative candidates;
- acceptance/rejection state plus deterministic reason;
- analysis policy version.

The record must use wording equivalent to “candidate” or “plausible
explanation,” never “proven cause.” Unavailable factors can support an
observability limitation but cannot serve as measured market causes.

## Gap classification semantics

### NO_GAP

The evaluation is fulfilled without material unexpected events and no
unexplained divergence is identified.

### MISSING_EXPECTED_REALITY

The evaluation establishes a genuine measured `MISSING` event. Provider absence
alone cannot produce this type.

### UNEXPECTED_REALITY

One or more material measured unexpected events exist even if the expected
criterion was fulfilled.

### CONTRADICTORY_REALITY

Measured evidence satisfies stored contradiction criteria.

### MIXED_GAP

Multiple material missing, unexpected, or contradictory dimensions coexist.

### OBSERVABILITY_GAP

Reality could not be determined adequately because required data was missing,
stale, unsupported, erroneous, temporally invalid, or insufficiently covered.
This normally aligns with `EXPIRED` but must be derived structurally, not by a
single status lookup.

### EXPLANATION_GAP

The expectation result is known, but eligible measured evidence does not
adequately explain the divergence. This differs from observability failure:
the formal event is known, while its explanation is weak or absent.

### UNKNOWN

Input consistency or structured metadata is insufficient for reliable gap
classification.

## Event groups

The output must preserve separate, ordered, duplicate-free groups:

- missing expected events: sufficiently measured expected events that did not
  occur;
- unexpected events: material facts outside fulfillment criteria;
- contradictory events: measured facts satisfying contradiction criteria.

Unavailable data must not be placed in a measured event group. It belongs in
observability limitations and evidence provenance.

## Evidence invariants

1. Expectation/evaluation/Timeline IDs and asset must match.
2. Evaluation must reference the exact expectation snapshot or a verifiably
   equivalent immutable record.
3. Eligible evidence timestamp is after the expectation source entry and no
   later than both expectation `window_end` and evaluation `evaluated_at`.
4. Evidence must be referenced by stable Timeline entry, delta, or trace ID.
5. AVAILABLE measured values remain distinct from missing/stale/unsupported/
   error states.
6. Current policy defaults cannot repair historical contract metadata.
7. Evidence outside the historical window cannot alter the analysis.
8. Identical immutable inputs and policy produce identical ordered output.
9. Input and previous output objects are never mutated.
10. Free-form text cannot create evidence or change classification.

## Temporal and relevance rules

A Root Cause Candidate is eligible only when its supporting evidence:

- existed at or before the classified gap/evaluation cutoff;
- is inside the authoritative evidence window;
- has a structured relationship to the affected criterion or event;
- is not merely a restatement of the result;
- is measured when presented as a market cause;
- preserves dependency/independence provenance.

Evidence after the divergence may be descriptive context only if the future
policy explicitly permits it and must never be labeled causal. Phase 1 should
prefer rejecting it entirely.

## Knowledge Gap Score requirements

Knowledge Gap measures unexplained divergence, not magnitude of divergence.
Any future 0..100 formula must:

- increase as unexplained residual or evidence conflict increases;
- increase as observability/completeness decreases;
- decrease as direct, temporally valid, independent cause candidates strengthen;
- avoid treating Surprise Score as a substitute for ignorance;
- distinguish “no gap” from “gap explained well”;
- define behavior for observability and explanation gaps;
- reject booleans and preserve deterministic rounding;
- be fully documented and covered by golden boundary/monotonicity tests.

No formula or threshold is approved in Step 7A.

## Explanation Confidence requirements

Explanation Confidence measures support for proposed candidates. Any future
0..100 formula must consider:

- evidence completeness and observability quality;
- temporal precedence;
- direct criterion relevance;
- independent supporting facts;
- candidate contradiction and rejected alternatives;
- remaining unexplained residual.

It must not represent market confidence, expectation correctness, trade
confidence, direction, or profitability. A record with no accepted cause
candidate cannot claim high Explanation Confidence.

## Severity requirements

Future deterministic severity policy may consider expectation strength,
evaluation status, Surprise Score, affected criteria count, stage/factor impact,
gap persistence, and observability limitations. It must document precedence and
avoid deriving financial or trading meaning. `CRITICAL` requires an explicit
architecture-approved criterion; it cannot mean merely “high Surprise.”

## Decision trace

The future output must contain or reference an immutable ordered trace with:

1. source identities and versions;
2. formal Evaluation result;
3. evidence window/cutoff and eligible entries;
4. primary and secondary gap classification reasoning;
5. cause categories considered in deterministic order;
6. accepted candidates and supporting evidence;
7. rejected candidates and reasons;
8. alternatives/conflicts/observability limitations;
9. unexplained residual;
10. inputs to Knowledge Gap, Explanation Confidence, and severity;
11. final classifications/metrics;
12. policy and contract versions.

Rendered prose may summarize the trace but cannot replace it.

## Anti-hindsight invariants

- exact expectation and evaluation IDs are mandatory;
- only evidence known by `evaluated_at` is eligible;
- expectation window and stored rule contract are authoritative;
- later policy versions cannot reinterpret old records;
- later evidence creates a new analysis version only;
- outcome data is excluded;
- historical analyses are never rewritten;
- all rejected and unresolved explanations remain visible.

## Learning boundary

The Reality Gap layer is stateless analysis, not learning. Future learning may
aggregate immutable analyses to study recurring expectation gaps, candidate
patterns, provider observability, or high-Surprise/low-confidence families. It
cannot mutate gap records or feed unreviewed weights back into the engine.

## Outcome boundary

Reality Gap is constrained to the expectation window. Outcome Analysis uses a
separate later horizon and separate contract. A later favorable or unfavorable
market result cannot change the earlier Evaluation or Reality Gap Analysis.

## Future implementation acceptance criteria

Before Step 7B implementation approval, the design must provide:

1. exact immutable model and enum definitions;
2. deterministic IDs, versioning, serialization, and UTC rules;
3. mapping for every Evaluation status/gap type;
4. candidate extraction/rejection policy for all seven Expectation rule
   families;
5. explicit observability-versus-explanation representation;
6. evidence-reference and temporal-precedence contract;
7. deterministic trace schema;
8. justified formulas or explicit “not calculated” semantics;
9. anti-hindsight and no-mutation tests;
10. missing/stale/unsupported/error tests;
11. no-prose-parsing and no-causation-claim tests;
12. Python 3.9 and standard-library-only boundary;
13. no provider, Telegram, database, production, persistence, learning, outcome,
    or network imports;
14. complete regressions proving existing contracts/pipeline unchanged.

## Unresolved policy questions

1. Should observability and explanation gaps be orthogonal flags plus a primary
   type, or a composable set of gap dimensions?
2. What exact evidence makes a candidate directly relevant to each of the seven
   rule families?
3. How should dependent factors be de-duplicated when assessing independent
   support?
4. Can evidence at the same timestamp establish temporal precedence, or only
   contemporaneous association?
5. How is unexplained residual represented before a numeric formula exists?
6. What deterministic thresholds separate severity levels, especially
   `CRITICAL`?
7. Should Knowledge Gap and Explanation Confidence initially be optional, or
   must Step 7B approve formulas before any runtime model exists?
8. How are multiple analyses of later Timeline versions linked without implying
   that old analyses were incorrect?
9. Which identity/evolution traces are guaranteed to be available as stable
   references?
10. What later persistence and retention policy preserves analyses without
    broadening Step 7 scope?

## Recommended next phase

Step 7B should be a contracts-and-policy design task. It should finalize the
immutable conceptual models, gap dimensionality, evidence references,
root-cause candidate taxonomy, trace schema, identity/version rules, and metric
decision (formula versus explicit uncomputed state). It should not integrate
production, persistence, Telegram, learning, or outcome analysis.
