# PS-4 Step 7C Report — Immutable Reality Gap Contracts & Validation

## Scope

Step 7C adds a standard-library-only, Python 3.9-compatible domain package for
immutable Reality Gap Analysis records. It implements approved Step 7A/7B
contracts and validation only. It does not implement analysis logic.

## Contracts created

- eleven enum taxonomies for dimensions, gap types, severity, evidence, and
  root-cause candidate state;
- `AnalysisProvenance` and `AnalysisCapabilities`;
- `RealityGapEvidenceReference`;
- `ObservabilityGapRecord` and `ExplanationGapRecord`;
- `RootCauseCandidate` and `RootCauseTree`;
- `RealityGapDecisionTrace` and `RealityGapAnalysis`;
- `validate_root_cause_tree`, `validate_analysis_revision`, and
  `canonical_json_bytes`.

## Provenance and capability semantics

Provenance records the engine, classification, candidate, metric, severity,
tree, trace, taxonomy, and serialization policy versions that produced a
record. `created_by` identifies software, not a person. Metadata is primitive,
deeply immutable, and rejects secret/credential/host/payload keys.

Capabilities declare what an engine version can represent. `False` means
unsupported, never “the gap did not exist.” Unsupported knowledge-gap,
explanation-confidence, tree, and severity outputs are required to be `None`.

## Validation and reference integrity

Contracts normalize aware datetimes to UTC, reject naive timestamps and
booleans used as numbers, validate scores in `0..100`, require stable IDs, and
deeply freeze mappings and collections. Evidence IDs and candidate IDs are
unique. Candidate and trace references must resolve. Measured zero remains
distinct from missing data, and unavailable evidence cannot carry a measured
value.

Candidate groups are disjoint, exhaustive, and aligned with dispositions.
Accepted groups include `ACCEPTED` and `PARTIALLY_SUPPORTED`; rejected and
unresolved dispositions retain separate groups.

## Tree integrity

The tree permits multiple roots and one accepted-tree parent per candidate.
It rejects missing references, cycles, self-edges, duplicate edges, multiple
parents, incorrect roots, disposition mismatches, parent/child disagreement,
and maximum-depth violations. Edge order is canonical and deterministic.

## Version lineage

An analysis revision preserves `gap_id`, expectation/evaluation/Timeline/asset
identity, the historical `evaluated_at` boundary, the decision trace evidence
window, and the eligible source Timeline versions and entry IDs. A revision
must increment by exactly one and include a reason. No record is overwritten
or automatically merged.

## Reproducibility guarantee

Every model supports deterministic primitive `to_dict()`/`from_dict()`.
`canonical_json_bytes()` uses UTF-8, sorted keys, compact fixed separators, and
rejects non-finite values. The package generates no IDs or current timestamps
and reads no host, locale, environment, network, or runtime state.

## Optional metrics

Knowledge gap, explanation confidence, residual, severity, tree, and related
policy versions remain optional as specified. Step 7C accepts already-declared
values but contains no metric, classification, severity, candidate-generation,
or evidence-extraction function.

## Dependency boundary

Runtime imports are limited to Python standard library modules and local
`app.intelligence.reality_gap` modules. The package does not import Expectation,
Evaluation, Timeline, Identity, Evolution, scanner, provider, exchange,
networking, Telegram, database, repository, production pipeline, Decision,
Trade Readiness, MarketStateEngine, Expert, learning, or Outcome Analysis code.
No dependency was added.

## Tests and verification

Focused `unittest` coverage exercises all enums, component round trips,
immutability, UTC/numeric validation, evidence eligibility, availability,
tree integrity, trace windows, complete analysis serialization, capability and
version agreement, source boundaries, revision lineage, forbidden domain
fields, deterministic dictionaries, and canonical JSON bytes. Existing
Expectation/Evaluation, Timeline/Evolution/Identity, Early Bird, intelligence,
and safe smoke suites are run before commit.

## Production impact

None. No production pipeline, Telegram, Hostinger, persistence, learning,
Outcome Analysis, requirements, or existing domain contract is modified.

## Open questions

- Step 7D must define who constructs eligible evidence references and assigns
  stable evidence/candidate IDs.
- Step 7D must decide whether externally generated rejected evidence is stored
  in the same evidence collection or a separately named audit collection.
- Policy owners must publish freshness and eligibility criteria before runtime
  construction begins.

## Recommended Step 7D

Design and review a deterministic Reality Gap assembly service that consumes
only approved snapshots and already-classified inputs. Keep classification,
metrics, candidate generation, and production integration outside that step
unless separately authorized.
