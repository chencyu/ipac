---
name: data-structure-design
description: "Must load before designing data structures, modeling state, or choosing how data is represented. Do not shape data representations without this skill."
---

# Data Structure Design

Complexity has to live somewhere. Put it in the **shape of the data**, not in the code that walks it. A representation chosen well makes the algorithm self-evident, the special cases vanish, and the illegal states become impossible to write down.

This is the operational expansion of *skill: design-principles* → "Data Structures Over Algorithms". That skill states the principle; this one is the procedure for reaching it.

## When This Skill Fires

After the problem is decomposed (*skill: thinking-principles*, *skill: problem-solving*) and **before** picking an algorithm (*skill: algorithm-selector*) or writing logic. Order matters: get the representation right first — the algorithm usually collapses into something obvious, and you may not need `algorithm-selector` at all.

**Skip this skill** when there is no modeling decision: formatting a string, gluing two APIs, a one-line config change.

## The Generating Core

The test of a good data structure is a property of the **code around it**: that code has no boundary branches and re-checks no invariant. If you are writing `if (empty)`, `if (head)`, `if (null)`, `if (first/last)`, or re-validating a rule a caller already enforced — the representation is wrong, not the code. Change the data until the branch becomes the general case.

## Protocol

### Step 1 — Model entities and relationships first
List the entities (nouns), each one's **identity** (what uniquely names it), and the **relationships** among them: 1:1, 1:N, N:M, ordering, hierarchy, graph. The relationships *are* the structure. Draw the tables before any flowchart (Brooks).

### Step 2 — Encode invariants into the type, not into checks
For each rule that must always hold, choose a representation where violating it is **unrepresentable**, not merely validated. Parse untrusted/loose input into a precise type **once, at the boundary**; downstream code then cannot re-fail. (Make illegal states unrepresentable; parse, don't validate.)

- `N` booleans = `2^N` states, most illegal → one enum / tagged union naming exactly the legal states.
- "list + dedupe check" → `Map`/`Set` keyed by identity.
- "value + range check repeated everywhere" → newtype with a smart constructor at the boundary.

### Step 3 — Shape for the dominant access pattern
Name the single most frequent or most performance-critical operation. Make **that** cheap by construction (index, sorted order, adjacency list, hash, precomputed view). State the trade-off you accepted. Do **correctness shaping** here; defer hardware/layout tuning to the gotcha below.

### Step 4 — Dissolve special cases (the good-taste test)
Walk every operation the structure supports. For each boundary branch, ask: *is there a representation where this branch is the normal case?* This is the highest-leverage step.
When you hit a recognizable smell, read [references/representation-patterns.md](references/representation-patterns.md) — a smell→move catalog (pointer-to-pointer, sentinel node, half-open interval, ring buffer, sum type, …). Apply the move, delete the branch.

### Step 5 — One source of truth; co-locate behavior with data
Every fact has exactly one authoritative home. Derived or denormalized views are generated from it or owned by one small module — never independent originals. Operations live where their data lives. (See *skill: design-principles* → Single Source of Truth.)

### Step 6 — Validate by re-deriving the operation
Sketch the core operation against the chosen structure. Short and obvious → the representation is right. Long, branchy, or re-checking invariants → still wrong; return to Step 1. The algorithm is the **acceptance test** for the data structure, not the other way around (Pike's Rule 5).

## Gotchas

- **A special case in code is a design smell, not a thing to handle carefully.** Before writing the branch, hunt for the representation that removes it.
- **Don't reach for a cleverer algorithm to rescue a painful structure.** Painful traversal means the data is shaped wrong. Reshape the data; the algorithm collapses.
- **Validation that returns nothing throws away what it learned** (`-> bool`/`-> void` then ignored), so the check gets scattered and repeated ("shotgun parsing"). Return the refined type instead.
- **Two phases, in order.** (1) *Correctness shaping* — unrepresentable illegal states, dissolved special cases — always first. (2) *Performance layout* — AoS↔SoA, cache packing, alignment (data-oriented design) — only **after** measuring a real bottleneck. Never let layout tricks obscure the model preemptively.
- **Denormalized / cached / duplicated data are drift seeds.** Two places holding the same fact is itself a representable illegal state (they desync). If duplication is unavoidable for speed, keep one source of truth behind one small module that owns synchronization.
- **Theory loses to practice.** If a textbook-clean structure fights the real data distribution, access pattern, or hardware, it is the wrong structure for *this* problem. Reshape to reality; don't force reality into the model.

## Why (the tradition)
When you need the rationale or a citable source for any rule above — Linus on "good taste", Pike's Rule 5, Brooks's tables, ESR's Rule of Representation, type-driven design — read [references/lineage.md](references/lineage.md).
