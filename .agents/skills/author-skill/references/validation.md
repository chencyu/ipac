# Validation

Run `skills-ref validate <skill-directory>`: exit 0 means valid; exit 1 prints errors to stderr. It checks `SKILL.md` existence, YAML parsing, required `name`/`description`, and only these frontmatter fields: `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`. `name` is lowercase alphanumeric plus hyphens, at most 64 characters, with no edge/consecutive hyphens, and matches the directory; `description` is nonempty and at most 1024 characters.

Other commands: `skills-ref read-properties <path>` emits frontmatter JSON; `skills-ref to-prompt <path> [<path> ...]` emits `<available_skills>` XML. The package is under `references/agentskills/skills-ref/`; for wrapper invocation, follow `references/platform-detection.md` and `scripts/validate-cli`.

Also inspect VS Code diagnostics on the `SKILL.md` or skill directory. If discovery still fails without diagnostics, open Chat's gear menu → `Show Agent Debug Logs` and inspect parser errors.
