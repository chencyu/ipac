---
name: design-principles
description: "Apply structural and architectural design principles before building anything — software, research methodology, data models, analysis frameworks. Use when deciding how to organize a system or structure a problem space. Applies to code architecture, research design, and data organization equally."
user-invocable: false
---

# Design Principles

Structural decisions come before implementation. Get the shape right; the logic follows.

## Architecture-Driven (over Logic-Driven)

Define components and their interfaces before writing logic. The structure of the system determines whether the logic is simple or complex.

Gotcha: Don't start implementing functions/steps until you know what the top-level components are and how they communicate. Logic written before structure becomes load-bearing spaghetti.

## Data Structures Over Algorithms

The right representation eliminates the need for complex processing. Invest more time in how data is shaped than in how it's traversed.

Gotcha: Before writing an algorithm, ask: is there a representation where this problem becomes trivial? A lookup table, adjacency list, or sorted index often replaces an O(n²) search.

In research: invest in how findings are organized (taxonomy, schema, ontology) before building analysis pipelines on top.

## Efficient Data Representation and Layout

Choose representations that make the common case cheap — in access patterns, cognitive load, and storage.

Gotcha: Redundant representations create synchronization debt; sparse representations create access overhead. Pick the one that fits the dominant use pattern, document the trade-off.

## Avoid Costly Abstractions

Every abstraction layer has a cognitive cost. Only introduce one if it simplifies actual usage, not hypothetical future usage.

Gotcha: "We might need this later" is not justification. Build the abstraction when the second concrete use case appears — not before. This applies equally to software interfaces and research taxonomy levels.
