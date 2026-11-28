---
name: author-skill
description: "Must load when creating, editing, reviewing, or validating any agent skill (SKILL.md). Do not author skills without this skill."
user-invocable: false
compatibility: "Requires git (for local spec sync). VS Code with GitHub Copilot. (Optional)"
---

# Author Skill

First, unconditionally fire-and-forget the platform script: `scripts/sync-spec.ps1` on Windows, `scripts/sync-spec.sh` elsewhere. Do not inspect its output or exit code.

Before anything else, read these in full:

1. `references/agentskills/docs/specification.mdx`
2. `references/agentskills/docs/skill-creation/best-practices.mdx`
3. `references/agentskills/docs/skill-creation/optimizing-descriptions.mdx`

Read `references/validation.md` when validating output and `references/platform-detection.md` when script paths vary by OS.

## Authoring

Before authoring, load `semantic-writing`. Apply its pipeline to skill files, references, and agent instructions before validation.

- **Description:** it is the always-visible classifier, not a summary. Use exactly `"Must load when/before [activity]. Do not [activity] without this skill."`: sentence one names a specific activity trigger; sentence two prohibits the same activity without the skill. No feature list, synonym coverage, soft "use when," or third sentence. Keep under 150 characters where possible.
- **Body:** retain only content the agent would otherwise get wrong: non-inferable gotchas, non-obvious ordered procedure, and references with explicit read conditions. What the agent does otherwise is its trained default, both where no provision covers a case and where one fits it poorly. So write a provision only where that default is wrong.
- **Abstraction:** a skill's body is the core that `skill: semantic-distillation` extracts from real domain material, not the cases that material records.
- **Files:** a page carries only what its own step needs; specs, schemas, examples, and templates live under `references/`, `scripts/`, or `assets/`. Split out a child page exactly when you can state the condition for reading it, and cite it with that condition. Nest to any depth, overriding the spec's one-level-deep guidance — as a skill grows, `SKILL.md` and the upper layers reduce to an index plus core statement while the substance sits at the leaves.
- **Length:** the specification's 500-line limit on `SKILL.md` is a hard limit. Strongly prefer under 50 lines, for `SKILL.md` and for every authored `.md` file reachable from it. Exceeding 50 lines is a signal to re-apply the split test in the "Files" bullet. It is not itself an order to split.

The frontmatter `name` must exactly match its directory or discovery fails silently. After every edit, validate with `references/validation.md`.
