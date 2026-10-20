---
name: code-craft-principles
description: "Must load before writing, reviewing, or refactoring any code. Do not produce or evaluate code without this skill."
user-invocable: false
---

# Code Craft Principles

Optimize for a future expert's comprehension, not brevity or cleverness.

- Code is authoritative for **what**; comments document only **why**. Rewrite unclear code instead of paraphrasing it in comments, which drift.
- Names and comments are read for meaning: write them under skill `semantic-writing`.
- Express constraints in types; use explicit errors and testable units. Validate untrusted input only at system boundaries, never recheck invariants already enforced by internal types.
- Give each function one purpose, summarized by its name; a name requiring “and” signals a split.
- Check preconditions with guard clauses and keep the happy path least indented.
- Reformulate or normalize inputs until one general path handles every case; a special-case branch is a competing implementation. Prefer dispatch maps or polymorphism to scattered `if/elif`, and arithmetic gating for parameter enablement.
- Declare variables near their use and keep bindings short-lived.
