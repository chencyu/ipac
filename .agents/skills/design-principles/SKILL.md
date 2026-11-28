---
name: design-principles
description: "Must load before designing any system, component, schema, or data model. Do not produce or evaluate designs without this skill."
user-invocable: true
---

# Design Principles

Choose structure and interfaces before logic.

## Single Source of Truth

Each data value, meaning, contract, and rationale has one authoritative home; every other occurrence is generated, referenced, or cached. Unify differently written copies of one fact, but keep identical text separate when the concepts evolve independently. Generate derivable representations; handwritten copies drift.

## Shape Before Processing

Choose data structures before algorithms: put behavior where its data lives and seek a representation that removes traversal complexity or branches. For research, shape the taxonomy or schema before analysis. Define components and communication before implementation so intent is expressed once by the architecture, not reinvented by each function.

## Boundaries

A boundary — function, type, module, interface, file — replaces what lies behind it with a name and a contract. What a user must hold to use it correctly crosses it and is its cost; what they no longer hold stays behind and is its value. Cut where the least crosses, and carry what crosses in signatures and types: a name only promises.

Read the use site with the inside closed. If correct use needs the inside, or the contract takes at least as much to hold as the body, the cut is misplaced: move it or remove it. Documenting a leak is mitigation: the cut stays misplaced.

## Cost

Shape representation and layout for the dominant access pattern while naming the redundancy-versus-access trade-off.

## Scope

Solve the requirement in front of you, not one development has not reached: an unreached requirement cannot be validated, and building for it fixes the design around a use that may never arrive. Generalize only when a second concrete use simplifies actual work, never for hypothetical reuse. Narrow the problem to what is being solved now, then solve that completely.

Restraint never licenses a worse solution. A clean structure and the right representation belong inside every scope, never to a later one; a branchy shortcut is unfinished work, not economy. Take the best solution the scope admits, preferring one a later requirement can extend over one that must be torn out. That preference is not a licence for hypothetical reuse: leave the seam, never build the mechanism behind it.
