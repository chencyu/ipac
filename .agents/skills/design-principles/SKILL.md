---
name: design-principles
description: "Must load before designing any system, component, or data model — code architecture, data schemas, research methodology, or analysis frameworks. Do not produce or evaluate designs without this skill."
user-invocable: false
---

# Design Principles

Structural decisions come before implementation. Get the shape right; the logic follows.

## Single Source of Truth

Every fact, semantic, contract, and contextual rationale in the system must have exactly one authoritative location. Other locations are derivations, references, or cached views — never independent originals. "Truth" here is broader than data values:

- **Data** — a value's authoritative record
- **Semantics** — where a concept's meaning is defined
- **Contract** — where an interface's promise lives
- **Context** — where a decision's rationale is recorded

This principle is the conceptual root of several others in this skill and in *skill: code-craft-principles*. They are not restatements of it — each carries its own concrete trigger — but they share this generative core: when something has more than one authoritative home, the homes drift, and the system loses a stable reference for what is true.

Gotcha: DRY's substance is SSOT, not literal duplication. Two snippets that look identical but encode independently-evolving concepts should stay separate; two snippets that look different but encode the same fact must be unified.

Gotcha: Hand-written copies of a derivable representation are drift seeds. If a binding, client, document, or constant table can be generated from the source, generate it — the source is the truth, the copy is a lie waiting to happen.

## Architecture-Driven (over Logic-Driven)

Define components and their interfaces before writing logic. The structure is the authoritative expression of the system's intent; logic written first invents that intent piecemeal in each function. (See *Single Source of Truth*.)

Gotcha: Don't start implementing functions/steps until you know what the top-level components are and how they communicate. Logic written before structure becomes load-bearing spaghetti.

## Data Structures Over Algorithms

The right representation eliminates the need for complex processing. Invest more time in how data is shaped than in how it's traversed. A well-chosen data structure is also the authoritative source for the operations around it: when unsure where a behavior should live, ask where its data lives. (See *Single Source of Truth*.)

Gotcha: Before writing an algorithm, ask: is there a representation where this problem becomes trivial? A lookup table, adjacency list, or sorted index often replaces an O(n²) search.

In research: invest in how findings are organized (taxonomy, schema, ontology) before building analysis pipelines on top.

## Efficient Data Representation and Layout

Choose representations that make the common case cheap — in access patterns, cognitive load, and storage.

Gotcha: Redundant representations create synchronization debt; sparse representations create access overhead. Pick the one that fits the dominant use pattern, document the trade-off.

## Avoid Costly Abstractions

Every abstraction layer has a cognitive cost. Only introduce one if it simplifies actual usage, not hypothetical future usage.

Gotcha: "We might need this later" is not justification. Build the abstraction when the second concrete use case appears — not before. This applies equally to software interfaces and research taxonomy levels.
