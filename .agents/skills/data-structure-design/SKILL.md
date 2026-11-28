---
name: data-structure-design
description: "Must load before designing data structures, modeling state, or choosing how data is represented. Do not shape data representations without this skill."
---

# Data Structure Design

Use after problem decomposition and before algorithm selection or logic; skip work with no modeling decision.

A sound representation makes surrounding code branchless at boundaries and prevents invariant rechecks. If code tests empty/head/null/first/last or repeats a caller's validation, reshape the data.

## Protocol

1. List entities, each identity, and relationships (1:1, 1:N, N:M, order, hierarchy, graph); draw tables before flows.
2. Make invariant violations unrepresentable in the type. Parse loose input once at the boundary into that type: replace boolean state combinations with an enum/tagged union, list-plus-deduplication with an identity-keyed map/set, and repeated range checks with a smart-constructed newtype.
3. Make the dominant or critical operation cheap by construction and state its trade-off. Shape correctness now; defer hardware/layout tuning until measurement proves a bottleneck.
4. Walk every operation and replace each boundary branch with a representation where it is ordinary. For a known smell, use `references/representation-patterns.md`, then delete the branch.
5. Give every fact one authoritative home, colocate operations with their data, and generate derived views. If speed requires duplication, one small owner must synchronize it.
6. Sketch the core operation. Short and obvious accepts the representation; long, branchy, or invariant-rechecking returns to step 1.

A cleverer algorithm cannot rescue painful traversal. Validation must return the refined type, not discard what it learned. Read `references/lineage.md` only when rationale or sources are needed.
