# PS-4 Classification and Metrics Boundary Specification

## Objective

Define the normative immutable boundary for future Classification and Metrics
consumers of approved Reality Gap artifacts, without implementing contracts,
algorithms, formulas, or runtime services.

## Scope

This specification defines:

- ownership and dependency boundaries;
- allowed historical inputs;
- conceptual classification and metric-set records;
- independent policy and record versioning;
- structured traces and typed failures;
- anti-hindsight and no-partial-result rules;
- future implementation acceptance boundaries.

## Out of scope

- Python runtime contracts or consumers;
- classification rules, category algorithms, metric formulas, scoring,
  ranking, confidence, or severity calculations;
- candidate, projection, mapping, evidence, tree, or assembler changes;
- causal explanation or RootCauseTree generation;
- persistence, learning, Outcome Analysis, providers, production, Telegram,
  Hostinger, deployment, or trading behavior.

## Normative terminology

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` describe requirements for a future
separately reviewed implementation. This task adds documentation only.

## Layer contract

```text
RootCauseCandidate + RealityGapContext + approved evidence references
                              |
                 +------------+------------+
                 |                         |
                 v                         v
       Classification Consumer       Metrics Consumer
                 |                         |
                 v                         v
 RealityGapClassification      RealityGapMetricSet
```

Both consumers are read-only. Neither may mutate an input or create candidate,
projection, mapping, evidence, explanation, tree, or analysis identity.

## Semantic separation

Classification MUST answer only: **What type of Reality Gap is represented?**

Metrics MUST answer only: **How measurable, observable, and explainable is
this Reality Gap?**

Neither MUST answer why the gap occurred. Explanation remains owned by
Candidate and RootCause layers. Neither result is a trading decision, causal
truth claim, certainty estimate, or action recommendation.

## Classification input

A future immutable request MUST contain or reference:

- request identity/version;
- one or more existing `RootCauseCandidate` identities and snapshots;
- exact candidate/projection/mapping lineage versions;
- immutable Reality Gap analysis/context identity and version;
- exact approved evidence references, when the policy requires them;
- classification-policy identity/version;
- caller-supplied aware UTC evaluation boundary;
- deeply immutable primitive metadata.

The request MUST NOT contain later Timeline entries, outcomes, learning
feedback, future evidence, hidden provider assumptions, mutable repositories,
or a current policy substituted for the historical policy.

## Conceptual `RealityGapClassification`

Required immutable fields:

- `classification_id: str`;
- `classification_policy_version: str`;
- `analysis_reference: str`;
- `dimensions: tuple[RealityGapDimension, ...]`;
- `categories: tuple[str, ...]`;
- `created_at: aware UTC datetime`;
- `trace_reference: str`;
- `metadata: immutable primitive mapping`.

Requirements:

- IDs, versions, analysis reference, and trace reference MUST be non-empty;
- dimensions and categories MUST use deterministic canonical ordering;
- duplicate dimensions/categories MUST be rejected;
- dimensions MUST use the existing vocabulary `MARKET`, `INTELLIGENCE`,
  `OBSERVABILITY`, and `EXPLANATION`;
- combined dimensions MAY be returned under an approved policy;
- category vocabulary MUST be owned/versioned by classification policy;
- timestamps MUST be timezone-aware and normalized to UTC;
- collections and metadata MUST be deeply immutable;
- serialization MUST preserve enums, timestamp, ordering, and lineage;
- canonical serialization MUST be deterministic.

Classification MUST NOT create a causal explanation, candidate, evidence
reference, metric, rank, confidence, severity, or tree relationship.

## Classification ownership

The Classification Layer owns policy selection/validation, category and
dimension assignment under that policy, classification record identity/version,
and `ClassificationTrace`. It owns no upstream artifact and cannot repair or
reinterpret one.

## Metrics input

A future immutable request MUST contain or reference:

- request identity/version;
- immutable Reality Gap analysis/context identity/version;
- exact RootCauseCandidate and approved evidence identities/versions required
  by each metric definition;
- metric-policy identity/version;
- explicit requested metric names;
- explicit availability/quality facts where approved inputs expose them;
- caller-supplied aware UTC measurement boundary;
- deeply immutable primitive metadata.

The consumer MUST NOT fetch providers, infer unavailable facts, fill missing
inputs with meaningful zeroes, use outcomes, or inspect future Timeline data.

## Conceptual `RealityGapMetricSet`

Required immutable fields:

- `metric_set_id: str`;
- `metric_policy_version: str`;
- `input_references: tuple[str, ...]`;
- `metrics: immutable ordered collection`;
- `created_at: aware UTC datetime`;
- `trace_reference: str`;
- `metadata: immutable primitive mapping`.

Each future metric value MUST preserve:

- metric name and metric-definition version;
- value only when measured;
- explicit availability state;
- units/domain and quality/provenance facts defined by policy;
- exact input references used;
- deterministic warnings, if any.

The metric set MUST be immutable, deterministic, versioned, serializable, and
round-trippable. Missing, stale, unsupported, and errored metrics MUST remain
distinct from a measured zero. No partial metric set is returned when the
request itself fails.

## Permitted metric subjects

An approved metric policy MAY measure:

- input/evidence availability;
- evidence or explanation coverage;
- observability;
- explanation completeness;
- evidence-quality indicators.

Metrics MUST NOT claim truth, causality, certainty, confidence, severity,
ranking, trade readiness, profitability, or actionability.

## Independent consumers

- Classification MUST NOT consume MetricSet output.
- Metrics MUST NOT consume Classification output.
- A shared input reference does not merge ownership.
- Classification MUST NOT infer a metric from a dimension/category.
- Metrics MUST NOT infer a dimension/category from a metric value.
- Either consumer MAY be unavailable while the other produces a valid result.
- A future derived consumer requires a separate architecture decision.

Example: an `OBSERVABILITY` dimension does not require a low observability
metric, and a low coverage metric does not create an `OBSERVABILITY` dimension.

## Versioning and identity

Classification-policy, metric-policy, input-object, analysis, result, and trace
versions MUST remain independent. Output identity material MUST include the
relevant policy and exact input identities/versions in canonical order. The
digest and encoding policy are deferred.

Any input or policy change MUST produce a new immutable result and trace.
Historical records MUST NOT be mutated or automatically reclassified/recomputed.

## Conceptual `ClassificationTrace`

Required structured fields:

- trace ID/version;
- request and analysis references;
- ordered candidate/mapping/evidence references and versions;
- classification-policy version;
- produced classification ID/version;
- ordered validation facts;
- ordered warnings;
- caller-supplied aware UTC creation time;
- immutable primitive metadata.

## Conceptual `MetricTrace`

Required structured fields:

- trace ID/version;
- request and analysis references;
- ordered metric input references and versions;
- metric-policy version and requested metric definitions;
- produced metric-set ID/version;
- ordered validation facts;
- ordered warnings;
- caller-supplied aware UTC creation time;
- immutable primitive metadata.

Traces MUST expose facts sufficient to reproduce policy application. They MUST
NOT store hidden reasoning, chain-of-thought, mutable objects, provider clients,
secret values, future facts, or post-outcome interpretation.

## Failure contract

Conceptual Classification failure categories:

- `INVALID_INPUT_REFERENCE`;
- `POLICY_MISMATCH`;
- `UNSUPPORTED_DIMENSION`;
- `VERSION_CONFLICT`.

Conceptual Metrics failure categories:

- `INVALID_INPUT_REFERENCE`;
- `UNSUPPORTED_METRIC`;
- `POLICY_MISMATCH`;
- `VERSION_CONFLICT`.

A future immutable failure MUST contain failure ID, category, request/policy
references, exact input lineage available for diagnosis, deterministic reason,
ordered validation facts/warnings, caller-supplied aware UTC timestamp, and
primitive metadata. A failure MUST contain no partial result. Consumers MUST
NOT silently skip invalid requested outputs or repair versions.

## Anti-hindsight rules

Consumers MUST:

- bind evaluation to an explicit caller-supplied aware UTC boundary;
- validate every referenced object/version and policy version;
- use only evidence approved for that historical boundary;
- reject later Timeline entries, future evidence, outcomes, and learning;
- preserve input lineage in result and trace;
- create new records rather than reinterpret historical output.

## Dependency boundary

Future runtime files MAY import Python standard library and approved immutable
local domain contracts. They MUST NOT import Telegram, FastAPI, databases,
repositories, providers, exchange clients, networking, pipelines, deployment,
persistence, learning, or Outcome Analysis.

## Assembly boundary

Assembly MAY validate and attach already-produced classification/metric records
under explicit capabilities and version agreement. Assembly MUST NOT classify,
calculate metrics, substitute defaults, or create traces. Changes to existing
Reality Gap or Assembly contracts require a separate reviewed task.

## Acceptance criteria for this design task

- exactly one ADR, one specification, and one report are added;
- the Classification and Metrics consumers are independent and read-only;
- ownership, input, output, version, trace, failure, and anti-hindsight rules
  are explicit;
- existing Reality Gap dimensions are preserved;
- no Python/runtime, classification, metric, formula, scoring, ranking,
  confidence, severity, persistence, learning, production, Telegram, or
  Hostinger change is included.

## Verification commands

```bash
git diff --check
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
git status --short
```

## Future phase

After Architecture Review, a separate task MAY define immutable classification
and metric contracts and pure read-only consumers. It MUST still exclude
learning, persistence, automatic causality, production integration, and any
unapproved change to Candidate, Projection, Mapping, Evidence Preparation, or
Reality Gap contracts.
