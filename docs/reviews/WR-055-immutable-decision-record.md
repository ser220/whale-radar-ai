# WR-055 — Immutable Decision Record Contract

## Purpose

Introduce the first immutable contract of the Decision Domain.

The Candidate Pipeline is responsible for discovering, validating, enriching,
and preparing trading opportunities.

Once a candidate becomes eligible for decision making, the Intelligence layer
must produce an immutable Decision Record.

This record represents the fact that a decision has been created.

It is not an execution request, exchange order, runtime state,
or learning artifact.

It is the canonical decision object that becomes the root of every
subsequent Decision Domain workflow.

---

## Responsibilities

The Decision Record shall:

- provide a globally unique Decision ID;
- reference the originating Candidate;
- reference the originating Situation;
- capture immutable decision metadata;
- expose immutable governance references;
- expose immutable evidence references;
- provide deterministic contract versioning.

---

## Non-Responsibilities

The Decision Record shall never:

- execute trades;
- manage runtime state;
- contain exchange-specific fields;
- contain TP/SL values;
- contain position management;
- mutate after creation.

---

## Position in Architecture

Observations

↓

Candidate Pipeline

↓

Decision Record

↓

Decision Runtime

↓

Execution

↓

Evaluation

↓

Learning

---

## Architectural Principles

- Immutable
- Versioned
- Deterministic
- Exchange-independent
- Runtime-independent
- Audit-friendly

---

## Future Expansion

Future Decision Domain components will consume this contract:

- Runtime Engine
- Governance Engine
- Execution Engine
- Evaluation Engine
- Learning Engine

without modifying the original Decision Record.

---

## Review Conclusion

The Immutable Decision Record becomes the canonical root object of the
Decision Domain and establishes a stable boundary between Candidate
Intelligence and all downstream decision workflows.
