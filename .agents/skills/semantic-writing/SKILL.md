---
name: semantic-writing
description: "Must load before writing or revising files or commit messages for human or AI readers. Do not write or revise such content without this skill."
user-invocable: false
---

# Semantic Writing

The always-on core in `.agents/instructions/semantic-writing.instructions.md` decides what to say and how to encode it. Content that outlives the conversation is read many times, so it also passes a fixed contract and a bounded audit.

**Pipeline:** contract → candidate by the core → bounded audit → delivery.

1. Read [contract.md](references/contract.md) before drafting or editing: it freezes the baseline and what every candidate must preserve.
2. Draft the candidate by the core.
3. Read [audit.md](references/audit.md) before delivering a changed artifact. An unchanged draft is a valid outcome; reduction is not a quota.

This skill, its references, the core instruction, and the auditor's instructions pass through the same pipeline; none exempts itself.