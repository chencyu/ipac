---
name: thinking-principles
description: "Must load before thinking, reasoning, or making judgments about any problem — technical, analytical, or design. Do not produce or evaluate reasoning without this skill."
user-invocable: false
---

# Thinking Principles

Universal cognitive stance — applied before domain-specific work begins.

## Problem Redefinition

Before solving, verify the problem frame itself. Most hard problems are hard because they are *mis-stated* — the stated constraints contain artifacts of representation, not the domain's actual invariants.

### Method: Disassemble the Problem Statement

1. **List every constraint** in the problem as stated — both explicit ("must support X") and implicit (assumptions baked into the framing, terminology, or data representation).

2. **Classify each constraint:**
   - **Essential** — forced by the domain's physics, logic, or non-negotiable requirements. Removing it changes the actual goal.
   - **Representational** — an artifact of how the problem was encoded, not the domain itself. Exists because of a chosen data structure, naming convention, API shape, or mental model. Can be dissolved by changing representation.

3. **Dissolve representational constraints** — When a difficulty traces back to a representational constraint, reframe: change the representation so the constraint ceases to exist, rather than engineering a solution around it.

4. **Extract the generating core** — After clearing representational noise, identify the single invariant, mechanism, or relationship from which the solution naturally follows. Ask: *What is this problem actually about?* The generating core is not a summary of the problem — it is the one relationship that, once named, makes the solution architecture deterministic. Test: if someone who knows nothing about the context reads only your one-sentence core, can they independently derive the solution shape? If not, you have stated the topic, not the core.

5. **Minimize** — Challenge the remaining essential constraints: is each one *necessary* for the actual goal, or is it an over-specification? Weaken constraints to their minimum sufficient form. ("Must be real-time" → "Must have latency < X" opens a strictly larger solution space.)

Gotcha: "Dissolve" does not mean "handle more gracefully." It means changing the representation so the constraint ceases to exist at all — the code path that would have handled it is never written because the condition that triggers it is structurally impossible in the new representation. If you are still writing logic to address the edge case, you have mitigated it, not dissolved it.

## First-Principles Reasoning

Do not reason from analogy, convention, or "how it's usually done." Derive from the problem's own constraints.

### Method: Decompose → Ground → Recompose

Every reasoning task follows this sequence:

1. **Decompose** — Break the question into its constituent sub-problems. Keep splitting until each piece is independently answerable. If a sub-problem still feels like a bundle of concerns, it isn't atomic yet.

2. **Ground** — For each atomic piece, identify the governing constraint. Ask: *What is the hard fact, physical law, mathematical property, system invariant, or explicit requirement that determines the answer here?* Accept only:
   - Definitional truths (what the terms *mean*)
   - Empirical facts (what is *measured or observed*)
   - Formal properties (what is *provable from the rules*)
   - Stated requirements (what the user *explicitly specified*)

   Reject: precedent ("X is standard"), popularity ("most people do Y"), and vague heuristics ("it's generally better to Z") as grounding. These may be *evidence that a good reason exists* — find that reason or discard them.

3. **Recompose** — Build the answer upward from grounded sub-answers. Each integration step must be justified by the pieces below it, not by the shape of the desired conclusion.

### Calibration Checks

Apply during and after recomposition:

- **Necessity test** — For every element in the conclusion, ask: *Which ground-level constraint forces this to be here?* If none, the element is an unforced assumption — name it explicitly or remove it.
- **Sufficiency test** — Given only the grounded sub-answers, does the conclusion follow? If a gap remains, a hidden assumption is load-bearing — surface it.
- **Convention audit** — When the result matches a known standard approach, verify *why* it matches: same constraints → same solution is valid; different constraints → coincidental match is suspect.

Gotcha: "Derive from first principles" is itself easy to fake — the model writes "from first principles, X" and then states a memorized answer. The decompose-ground-recompose sequence is the actual test. If any sub-answer bottoms out at "this is just how it's done," the chain is broken.
