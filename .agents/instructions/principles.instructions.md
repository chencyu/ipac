---
applyTo: '**'
---

# Principles

## I. Cognitive Stance

* Problem Redefinition: Before solving, audit the problem frame — classify constraints as essential (domain-forced) or representational (encoding artifact) and dissolve the latter by changing representation.
* First-Principles Derivation: Derive from the problem's own constraints. Reject convention, analogy, and precedent as grounding — they may point to a reason, but are not the reason.
* Pragmatism Over Purity: Optimize for the actual constraint space, not an idealized one.
* Expert-Centric Clarity: Assume domain expertise; use precise terminology without over-explanation.

## II. Structure & Implementation

* Architecture Before Logic: Define components and interfaces before writing logic.
* Data Structures Over Algorithms: The right representation eliminates complex processing.
* Avoid Premature Abstraction: Abstract when the second use case appears, not before.
* Self-Explanatory Code: Document 'Why', not 'What'.
* Unified Logic Paths: Eliminate special cases by reformulating; prefer maps/dispatch over if/else; exit early via guard clauses.

## III. Skills Driven Agent

* Always evaluate whether any agent skill description matches the current task; if yes, load it.
