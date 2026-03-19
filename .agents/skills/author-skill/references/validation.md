# Validation

Verify that a skill's SKILL.md conforms to the Agent Skills specification.

## CLI — `skills-ref validate`

Primary format validator. Checks:
- SKILL.md exists
- YAML frontmatter parses correctly
- Required fields present (`name`, `description`)
- `name`: lowercase, no leading/trailing hyphens, no consecutive hyphens, alphanumeric + hyphens only, max 64 chars, must match directory name
- `description`: non-empty, max 1024 chars
- No unexpected frontmatter fields (only `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility` allowed)

```
skills-ref validate <path-to-skill-directory>
```

Exit code `0` = valid, `1` = errors (printed to stderr).

Additional subcommands:
- `skills-ref read-properties <path>` — JSON dump of parsed frontmatter
- `skills-ref to-prompt <path> [<path> ...]` — generate `<available_skills>` XML block

The `skills-ref` package lives in `references/agentskills/skills-ref/`. For script-based invocation → see [platform-detection.md](./platform-detection.md) and `scripts/validate-cli`.

## VS Code — diagnostics & discovery

VS Code may surface frontmatter or format issues as diagnostics (warnings/errors). Two approaches:

1. **Diagnostics check**: use `get_errors` on the SKILL.md file (or its parent skill directory). If diagnostics appear for files under skill-related paths (`.agents/skills/`, `.github/skills/`, etc.), inspect the reported messages for format violations.
2. **Debug logs**: if no diagnostics but skill still missing → gear icon in Chat view → `Show Agent Debug Logs` to see parsing errors.
