# PS-4 Step 7G Report — Immutable Candidate Generation Boundary

## Summary

Step 7G defines the documentation-only boundary for immutable,
evidence-referenced candidate hypotheses. It assigns candidate identity and
version ownership, defines lifecycle/evidence semantics, separates hypotheses
from Root Cause Trees, and preserves anti-hindsight without implementing a
generator, causal detector, rank, confidence, classification, or metric.

## Candidate boundary

```text
Prepared Evidence References
            |
            v
Immutable Candidate Boundary
            |
            v
CandidateHypothesis
            |
            v
Future Explanation / RootCauseTree
```

The future boundary validates already-prepared hypothesis material. Step 7G
contains no algorithm that discovers or creates causes automatically.

## Candidate ownership

The Candidate Layer owns `candidate_id` and append-only candidate versions. It
validates immutable evidence references, creates hypothesis records, preserves
support/contradiction/limitations, and exposes stable IDs to future explanation.

It does not own evidence preparation, gap/trace/tree IDs, final disposition,
classification, metrics, severity, ranking, confidence, learning, persistence,
notifications, or production decisions.

## Candidate identity

Versioned identity material includes candidate namespace, category, subject,
stable hypothesis reference, and canonical identity-bearing eligible support
IDs. Same normalized hypothesis/support material produces the same candidate
ID. Identity is independent of time, UUID, database, process, host,
environment, locale, network, and mapping order. Digest/encoding is deferred.

## Candidate lifecycle

`CandidateStatus` values are `CREATED`, `SUPPORTED`, `CHALLENGED`, `REJECTED`,
and `UNRESOLVED`. They are lifecycle facts—not truth values.

Status is separate from analysis-specific `RootCauseDisposition`; Step 7G
defines no automatic mapping. Every allowed change creates the next immutable
candidate version. Identity-bearing changes create a new candidate lineage.

## Evidence requirements and semantics

Supporting evidence must resolve, remain eligible, predate creation within the
approved boundary, and be unique. Contradicting evidence must resolve and may
remain eligible or ineligible. Limitations preserve missing/unavailable and
observability facts without fabricated evidence.

Support means “consistent with the hypothesis,” not proof. Contradiction means
“inconsistent with the hypothesis,” not impossibility. No final truth,
relevance, confidence, or rank is evaluated.

## RootCauseTree relationship

Candidate hypotheses are tree-agnostic. The future Explanation Layer owns roots,
edges, positions, and analysis-specific dispositions. Trees reference IDs and
cannot mutate hypotheses; one hypothesis may appear in multiple structures.

The approved assembly `RootCauseCandidate` currently contains tree linkage and
does not contain conceptual candidate version/status. A future reviewed mapping
must project immutable hypotheses plus explanation decisions into that assembly
record. Runtime generation is blocked until this compatibility is resolved.
No approved contract was modified in Step 7G.

## Candidate trace

The conceptual trace records generation/policy identities, evidence and
candidate counts, validation results, deterministic warnings, supplied UTC
timestamps, and optional failure facts. It contains no hidden reasoning or
causal narrative.

## Anti-hindsight

Only approved evidence and its existing eligibility inside the original
analysis boundary may be used. Future evidence, later Timeline entries,
outcomes, learning feedback, historical similarity, boundary expansion, and
mutation of completed versions are forbidden.

## Failure model

Initial categories are `INVALID_EVIDENCE_REFERENCE`,
`INELIGIBLE_SUPPORTING_EVIDENCE`, `DUPLICATE_IDENTITY`,
`POLICY_VERSION_CONFLICT`, `INVALID_HYPOTHESIS_REFERENCE`, and
`INVALID_METADATA`. Failure preserves a reason, creates no partial candidate,
upgrades no evidence, and mutates no existing version.

## Alternatives

- assembler generation: rejected because construction and hypothesis mix;
- tree generation: rejected because hypotheses couple to one tree;
- provider causes: rejected because provider assumptions leak;
- dedicated immutable Candidate Boundary: selected.

## Production impact

None. Step 7G adds documentation only. No Python/runtime candidate generator,
algorithm, Reality Gap contract, provider, classification, metric, persistence,
learning, production pipeline, Telegram, Hostinger, or Outcome Analysis change.

## Open questions

- Should additional eligible support retain a candidate lineage or create a new
  identity after a future identity-policy review?
- What canonical hypothesis-reference format and namespace taxonomy are used?
- Which digest/encoding and collision policy will implement candidate IDs?
- How will `CandidateHypothesis` map immutably to approved assembly
  `RootCauseCandidate` fields, especially parent/child linkage?
- Which reviewed policy maps lifecycle status to analysis disposition without
  classification leakage?

## Recommended Step 7H

Before implementing classification or metrics, define the immutable mapping
from candidate hypotheses and explanation structures into the existing assembly
projection. Then design classification/metric policies as consumers of already
prepared evidence and candidates, with explicit inputs, versioning,
anti-hindsight, and no production integration.
