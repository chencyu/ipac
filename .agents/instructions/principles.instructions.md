---
applyTo: '**'
---

# Principles

## I. Cognitive Stance

* See the Invariant: Before solving, audit the problem frame — classify constraints as essential (domain-forced) or representational (encoding artifact). Dissolve the latter by changing representation so the constraint ceases to exist, not by handling it.
* Intrinsic Derivation: Reason from the problem's own constraints — definitional truths, measured facts, formal properties, stated requirements. Reject convention, analogy, and precedent as grounding; they may point to a reason, but are not the reason.
* Pragmatism Over Purity: Optimize for the actual constraint space, not an idealized one.
* Expert-Centric Clarity: Assume domain expertise; use precise terminology without over-explanation.

## II. Structure & Implementation

* Architecture Before Logic: Define components and interfaces before writing logic.
* Representation Over Processing: The right data shape eliminates complex algorithms and retires whole branches before they are written.
* Unified Path Over Special Cases: Reformulate until the general path handles every input. If an `if special_case:` branch is being considered, the representation is wrong.
* Avoid Premature Abstraction: Abstract when the second use case appears, not before.
* Self-Explanatory Code: Document 'Why', not 'What'.

## III. Skills Driven Agent

* Always evaluate whether any agent skill description matches the current task; if yes, load it.
