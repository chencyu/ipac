# First Principles Agent Context Engineering (F-PACE)

Context engineering is a settled idea. Most serious practitioners agree: what determines whether an agent succeeds is not the model, but the quality of its context. The conversation has moved on from prompting.

What has not moved on is the underlying assumption about what context is for.

## The Assumption

The prevailing approach treats context as information delivery. Retrieve the right documents. Provide the right tools. Write the right instructions. The implicit model is: the agent already knows how to think — you just need to give it what to know.

F-PACE starts from a different premise. A model's judgment is shaped by its training distribution, not by the task in front of it. When you ask it to reason about code, it reasons the way most code discussions reason. When you ask it to design a system, it reaches for the patterns that dominate its training. Its epistemology is inherited, not chosen.

Context is not just information. It is the opportunity to supply a different way of thinking.

## What Skills Encode

The skills in this repository do not tell the model what to do. They give it a framework for judgment that it would not have by default.

A thinking-principles skill does not say "follow these steps." It encodes the cognitive posture — derive from fundamentals rather than convention, prefer the simpler answer that solves the problem cleanly over the general answer that solves every case. A code-craft skill does not enumerate rules. It encodes how an expert reads code: what questions to ask, what signals matter, where complexity hides. A design-principles skill does not describe patterns. It encodes the reasoning that produces good architecture before a line is written.

The distinction matters because rules are followed. Frameworks are internalized. A model following a rule stops when the rule runs out. A model reasoning from a framework continues reasoning.

## Why First Principles

First principles, here, means two things simultaneously.

The skills encode ways of thinking that derive from first principles — not "do it this way because it works" but "do it this way because the underlying problem demands it." The goal is for the model to be able to rediscover the right answer from the framework, not to pattern-match against a checklist.

And the construction of the skills themselves follows first principles. A context window is finite and shared. Different content has different load guarantees depending on when and how it enters the model's context. These are physical constraints, not preferences. The architecture of each skill — what goes in the body, what stays in references, how the description is written — follows from those constraints, not from convention.

## This Repository

F-PACE is a working system built from these ideas. Each skill is a single domain of judgment, designed to activate on relevance and to supply a way of thinking rather than a set of instructions. Agents compose these frameworks into contexts appropriate for specific kinds of work.





