---
name: author-skill
description: "Must load when creating, editing, reviewing, or validating any agent skill (SKILL.md). Do not author skills without this skill."
user-invocable: false
compatibility: "Requires git (for local spec sync). VS Code with GitHub Copilot. (Optional)"
---

# Author Skill

Unconditionally execute the platform-appropriate sync-spec script ([PowerShell](scripts/sync-spec.ps1) on Windows, [Bash](scripts/sync-spec.sh) elsewhere) as the first action.
Do not inspect its output or exit code — fire and forget.
**This step is mandatory and will be moved into a *skill hook* once that mechanism is supported.**

## References

Agent skills is a post-training concept — read the following before doing anything else.

### Mandatory (read in full before starting)

1. [Skill Specification](references/agentskills/docs/specification.mdx) — format, frontmatter fields, directory structure
2. [Best Practices](references/agentskills/docs/skill-creation/best-practices.mdx) — what separates useful skills from vague filler
3. [Optimizing Descriptions](references/agentskills/docs/skill-creation/optimizing-descriptions.mdx) — how the description classifier works

### On-demand (read only when the trigger applies)

- Validating output → [Validation Guide](references/validation.md)
- Script paths differ by OS → [Platform Detection](references/platform-detection.md)

---

## Authoring Constraints

A skill has three layers with different visibility and cost. When authoring or editing a skill, ensure the output satisfies these constraints:

### Description — write it as a classifier, not a summary

The agent sees `name` + `description` (~100 tokens) for every installed skill and classifies: load or skip. The body is invisible until that decision is made.

**Required template — all descriptions in this repo must follow this exact structure:**

```
"Must load when/before [activity]. Do not [activity] without this skill."
```

Rules:
- **Sentence 1** — mandatory trigger: `Must load when/before` + the activity phrase that requires this skill. Be specific about the activity, not about the skill's contents.
- **Sentence 2** — mandatory inhibitor: `Do not` + the same activity phrase + `without this skill.` Mirror sentence 1's activity in negative form.
- No feature lists, no synonym coverage, no "use when" softeners. The classifier decides from the activity shape alone.
- Keep total description under 150 characters where possible.

Gotcha: Do not add a third sentence describing what the skill does. That content belongs in the body, not the description.

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
