---
name: author-skill
description: "Author or improve an agent skill — create new skills, refine existing ones, or extract reusable skills from conversations. Use when the user wants to build, edit, review, or package a skill, even if they say 'make this reusable', 'package this workflow', or 'turn this into a capability'."
user-invocable: false
compatibility: "Requires git (for local spec sync). VS Code with GitHub Copilot. (Optional)"
---

# Author Skill

## References

Agent skills is a post-training concept — read the following before doing anything else.

### Mandatory (read in full before starting)

1. [Skill Specification](references/agentskills/docs/specification.mdx) — format, frontmatter fields, directory structure
2. [Best Practices](references/agentskills/docs/skill-creation/best-practices.mdx) — what separates useful skills from vague filler
3. [Optimizing Descriptions](references/agentskills/docs/skill-creation/optimizing-descriptions.mdx) — how the description classifier works

### On-demand (read only when the trigger applies)

- Running sync → [Sync Guide](references/sync.md)
- Validating output → [Validation Guide](references/validation.md)
- Script paths differ by OS → [Platform Detection](references/platform-detection.md)

---

## Authoring Constraints

A skill has three layers with different visibility and cost. When authoring or editing a skill, ensure the output satisfies these constraints:

### Description — write it as a classifier, not a summary

The agent sees `name` + `description` (~100 tokens) for every installed skill and classifies: load or skip. The body is invisible until that decision is made.

When writing a description: use the **user's vocabulary** — the words they'd actually type. Cover synonyms and near-miss phrasings. Example: a user who says "turn this chat into something reusable" needs a description that covers "reusable", "package", "extract" — matching their intent, even when they never say "skill".

### Body — earn every token

The body shares the context window with conversation history, other active skills, and file contents. Apply this filter to every line you write: *"Would the agent get this wrong without this?"* If no — cut it.

What earns its place:
1. **Gotchas** — concrete corrections to mistakes the agent can't infer
2. **Procedure** — sequenced steps, only when order matters and isn't obvious
3. **Conditional references** — "Read `X` **if** Y" with a specific trigger condition

### Files — carry large payloads out of the body

Specs, schemas, examples, templates — anything large belongs in `references/`, `scripts/`, or `assets/`. The body says *when* and *why* to read a file; the file carries the payload.

---

## Gotchas

**`name` must match the parent directory name exactly.** A mismatch causes silent failure — the skill never loads, no error message.

**Ground every skill in real material.** Ask the user for conversation traces, runbooks, error logs, or past corrections before authoring. Domain-specific input is what separates a useful skill from vague filler.

**Validate after every edit.** See [Validation Guide](references/validation.md) for CLI and VS Code methods.
