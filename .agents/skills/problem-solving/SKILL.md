---
name: problem-solving
description: "Must load when solving problems, debugging, diagnosing failures, or choosing between solution approaches. Do not solve problems without this skill."
user-invocable: true
---

# Problem-Solving

Use these tools only after the problem frame is set.

- **Inversion:** before solving forward, enumerate what would guarantee failure; for each condition, require a structural reason it cannot occur, not an intention to avoid it. Apply this especially when the forward path seems obvious.
- **Second-order thinking:** for each direct effect, ask what it causes. Stop outside your control or when effects become negligible, and never reason beyond two levels; record concerning uncertainty as an assumption instead.
- **Root-cause analysis:** state the observable symptom precisely, then repeatedly ask why until reaching a changeable design decision, an immutable external constraint, or a missing invariant. Verify that fixing it prevents the entire failure class; if an analogous input can still fail analogously, you found a symptom, not the root.
