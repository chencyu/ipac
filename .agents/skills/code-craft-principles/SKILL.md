---
name: code-craft-principles
description: "Must load whenever writing, reviewing, or refactoring any code — new features, bug fixes, code review, or any implementation task. Do not produce or evaluate code without this skill."
user-invocable: false
---

# Code Craft Principles

Applied during implementation. These govern how code is written once structure is decided.

## Readability and Simplicity

The primary reader is a future expert. Optimize for fast comprehension, not brevity or cleverness.

## Self-Explanatory Code — Document 'Why', Not 'What'

Code is the authoritative source for *what* happens; comments are the authoritative source for *why* a decision was made. A comment that paraphrases what the code does duplicates that authority and will drift. If the *what* is unclear, fix the code. (See *Single Source of Truth* in *skill: design-principles*.)

Gotcha: A comment like `# increment counter` is noise. A comment like `# offset by 1 because downstream expects 1-indexed IDs` is signal.

## Verifiable Robustness

Use type hints, explicit errors, and testable units. When the type system can express a constraint, the type system is its authoritative home; a runtime guard on the same constraint is duplicate enforcement. (See *Single Source of Truth* in *skill: design-principles*.)

Gotcha: Only validate at system boundaries (user input, external APIs, deserialization). Validating internal invariants that the type system already enforces is dead code and misleads the reader about what can actually go wrong.

## Short, Focused Functions (Single Responsibility)

A function does one thing. The function's name is the authoritative summary of its behavior — if naming it requires "and", that summary is covering two things and is no longer single. Split it. (See *Single Source of Truth* in *skill: design-principles*.)

## Guard Clauses (Early Exit)

Validate preconditions at the top of the function. Return or raise early. Keep the happy path at the lowest indentation level.

Gotcha: Nested `if` chains inside a function body indicate missing guard clauses at the top.

## Unified Logic Paths (The Linus Taste)

Eliminate special cases by reformulating until the general path handles all inputs. The main path should be the sole authoritative implementation; a special-case branch creates a competing source of truth that every future change must remember to visit. (See *Single Source of Truth* in *skill: design-principles*.)

Gotcha: Before adding an `if special_case:` branch, ask whether the general logic can be extended or the input can be normalized upstream to make the special case disappear. Special cases indicate a leaky abstraction boundary.

## Branch Avoidance

Before writing `if/else`, ask whether a map lookup, arithmetic gating, or polymorphism eliminates the branch entirely. Scattered `if/elif` chains encode the routing rule separately in each branch — it has no single home. A dispatch table or polymorphic call gives that rule one authoritative location. (See *Single Source of Truth* in *skill: design-principles*.)

- Use dicts/maps for dispatch: `handlers[event_type](payload)` over `if/elif` chains.
- Use arithmetic gating for parameter enablement: `result = enabled * value` over `if enabled: result = value`.

## Minimize Variable Scope

Declare variables as close to their use as possible. Prefer short-lived bindings. A variable visible for 200 lines when it's only needed for 5 is a maintenance hazard.
