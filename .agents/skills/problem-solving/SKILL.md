---
name: problem-solving
description: "Must load when solving problems, debugging, diagnosing failures, or choosing between solution approaches. Do not solve problems without this skill."
user-invocable: false
---

# Problem-Solving

Tactical tools for working on a defined problem. Load after the problem frame is set (see thinking-principles for frame-level work).

## Inversion

Before solving forward, solve backward: *What would guarantee failure?* List the conditions, then verify your approach avoids every one of them.

This is not brainstorming risks — it is a systematic negation. For each failure condition, the solution must contain a structural reason it cannot occur, not merely an intention to avoid it.

Gotcha: Inversion is highest-value when the forward path feels obvious. "Obviously we should do X" is exactly when you need "What would make X catastrophically wrong?" — because the obvious path is where blind spots hide.

## Second-Order Thinking

Trace the consequences of your proposed solution one level further: *And then what?*

For each direct effect of the solution, ask what it causes in turn. Stop when the chain reaches components outside your control or when the effects become negligible. The goal is not infinite regress — it is catching the one non-obvious downstream effect that invalidates the approach.

Gotcha: Limit to two levels deep. Beyond that, confidence drops below usefulness and the analysis becomes speculative fiction. If a second-order effect is concerning but uncertain, name it as an explicit assumption rather than chasing third-order chains.

## Root Cause Analysis

When diagnosing a failure, do not stop at the proximate trigger. Ask *why* iteratively until you reach a cause that, if fixed, prevents the entire class of failure — not just this instance.

### Method

1. **State the symptom** — the observable failure, precisely. Not "it's broken" but "function X returns null when input Y has property Z."
2. **Ask why** — what condition directly causes this symptom?
3. **Repeat** — for each answer, ask why that condition exists. Continue until you reach one of:
   - A design decision that can be changed
   - A constraint that is genuinely external and immutable
   - A missing invariant that should be enforced but isn't
4. **Verify the root** — if you fix this cause, does the entire failure class disappear? If only this instance disappears, you are still at a symptom.

Gotcha: The most common trap is stopping one level too early — fixing the proximate cause feels productive but leaves the structural defect intact. The test: after your fix, can a similar (but not identical) input trigger an analogous failure? If yes, you fixed a symptom.
