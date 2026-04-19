# Intrinsic Paradigm for Agentic Cognition

Context engineering is a settled idea. Most serious practitioners agree: what determines whether an agent succeeds is not the model, but the quality of its context. The conversation has moved on from prompting.

What has not moved on is the underlying assumption about what context is for.

## The Assumption

The prevailing approach treats context as information delivery. Retrieve the right documents. Provide the right tools. Write the right instructions. The implicit model is: the agent already knows how to think — you just need to give it what to know.

This repository starts from a different premise. A model's judgment is shaped by its training distribution, not by the task in front of it. When it faces a legal argument, it argues the way most legal arguments argue. When it designs a system, it reaches for the patterns that dominate its training. When it reads a poem, analyses a market, advises on a decision — the shape of the reasoning is inherited, not chosen. Its epistemology is borrowed.

Context is not just information. It is the opportunity to supply a different way of seeing.

## The Stance — See the Intrinsic

The posture encoded here is a single move, the same across every domain: *see what is intrinsic to the situation, and let the structure that follows do the rest.*

Most hard problems are hard because they are being viewed in the wrong frame. The constraints that seem to complicate them are mixed from two sources — those forced by the subject itself, and those that are artifacts of how the subject happened to be described. Surface difficulty usually traces back to the second kind. The expert move is not to manage it more skilfully but to change how the situation is represented until that difficulty no longer exists. Special cases are not handled; they are dissolved. The general path, once found, carries every instance without a branch.

The stance is indifferent to domain:

- A judge who stops asking "was the conduct lawful?" and asks instead "whose interest is the rule actually protecting?" has replaced a rule-shaped frame with a purpose-shaped one, and the hard cases resolve themselves.
- A therapist who reframes "the patient keeps failing" as "the goal was the wrong goal" changes the object of the intervention, and the apparent resistance disappears.
- A physicist who sees electricity and magnetism as one field, not two forces, no longer has two sets of equations to reconcile.
- An engineer who stops treating the head of a linked list as a special case and sees every node as pointed-to by *some* pointer writes the general case and deletes the branch.

The surface vocabulary differs — doctrine, case formulation, unification, taste — but the move is the same. Identify what is intrinsic to the situation. Change the representation until that intrinsic becomes visible. Let the elegant answer emerge as the only thing the new frame can produce.

## What the Skills Encode

The skills do not tell the model what to do. They supply a framework of judgment it would not have by default.

The skill for thinking does not say "follow these steps." It encodes the move — find the representational constraints, dissolve them, name the generating core from which the answer follows. The skill for analysis does not prescribe a method. It encodes how an expert looks at a claim: which pieces are load-bearing, which are scaffolding, where a reframing would retire half the argument. The skill for design does not describe patterns. It encodes the judgment that the shape of the object decides the shape of the work done on it — and that the shape is chosen before the work begins.

Rules are followed. Frameworks are internalized. A model following a rule stops when the rule runs out. A model reasoning from a framework continues reasoning — because the framework is about how to *see*, and seeing does not run out.

## Why the Architecture Follows the Same Stance

The skills themselves are built under the same discipline. A context window is finite and shared. Different content has different load guarantees depending on when and how it enters the model's context. These are physical constraints, not preferences.

What goes in a skill's body, what stays in `references/`, how the description is written — each of these follows from the constraints, not from convention. The repository practices what it encodes: the structure is chosen so the rules it would otherwise need disappear.

## This Repository

A working system built from one stance. Each skill is a single domain of judgment, activated on relevance and supplying a way of seeing rather than a set of instructions. Agents compose these frameworks into contexts appropriate for any kind of work — technical, analytical, creative, advisory.

The stance has an older name — Aristotle's first cause, the intrinsic principle from which the rest follows. In different crafts it surfaces as *invariant*, *canonical form*, *taste*, *insight*, *reframing*. The name on the door is **Intrinsic Paradigm** because that is what the inside actually does, across any subject it is pointed at: start from the intrinsic, and let the paradigm emerge.

