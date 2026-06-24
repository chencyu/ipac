#!/usr/bin/env bash
set -euo pipefail

# Equivalent of link-ipac.ps1 for Linux/macOS.
# Creates symlinks for skills/agents/instructions into the selected agent directory.

usage() {
    cat <<'EOF'
Usage: link-ipac.sh [-a AGENT] [-d AGENT_DIR_NAME]

Options:
  -a AGENT            Agent profile: agent | claude | codex | github | copilot (default: agent)
  -d AGENT_DIR_NAME   Override agent directory name: .agents | .claude | .codex | .github | .copilot
  -h                  Show this help message
EOF
}

AGENT="agent"
AGENT_DIR_NAME=""

while getopts ":a:d:h" opt; do
    case "$opt" in
        a) AGENT="$OPTARG" ;;
        d) AGENT_DIR_NAME="$OPTARG" ;;
        h) usage; exit 0 ;;
        \?) echo "Invalid option: -$OPTARG" >&2; usage; exit 1 ;;
        :) echo "Option -$OPTARG requires an argument." >&2; usage; exit 1 ;;
    esac
done

case "$AGENT" in
    agent|claude|codex|github|copilot) ;;
    *) echo "Invalid agent: $AGENT" >&2; usage; exit 1 ;;
esac

if [ -n "$AGENT_DIR_NAME" ]; then
    case "$AGENT_DIR_NAME" in
        .agents|.claude|.codex|.github|.copilot) ;;
        *) echo "Invalid agent dir name: $AGENT_DIR_NAME" >&2; usage; exit 1 ;;
    esac
fi

# Resolve agent profile fields: <default_dir_name> <skills> <agents> <instructions>
default_dir_name=""
skills_dir_name="skills"
agents_dir_name="agents"
instructions_dir_name="instructions"

case "$AGENT" in
    agent)
        default_dir_name=".agents"
        instructions_dir_name="instructions"
        ;;
    claude)
        default_dir_name=".claude"
        instructions_dir_name="rules"
        ;;
    codex)
        default_dir_name=".agents"
        instructions_dir_name="instructions"
        ;;
    github)
        default_dir_name=".github"
        instructions_dir_name="instructions"
        ;;
    copilot)
        default_dir_name=".copilot"
        instructions_dir_name="instructions"
        ;;
esac

agent_dir_name="${AGENT_DIR_NAME:-$default_dir_name}"

# Resolve directories.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IPAC_DIR="$(dirname "$SCRIPT_DIR")"
AGENT_DIR="$HOME/$agent_dir_name"

add_agent_entries() {
    local entry_type="$1"
    local link_entry_type

    case "$entry_type" in
        skills) link_entry_type="$skills_dir_name" ;;
        agents) link_entry_type="$agents_dir_name" ;;
        instructions) link_entry_type="$instructions_dir_name" ;;
        *) echo "Unknown entry type: $entry_type" >&2; return 1 ;;
    esac

    local source_dir="$IPAC_DIR/.agents/$entry_type"
    if [ ! -d "$source_dir" ]; then
        return 0
    fi

    local target_parent="$AGENT_DIR/$link_entry_type"
    mkdir -p "$target_parent" &> /dev/null

    local entry name link_path
    for entry in "$source_dir"/*; do
        [ -e "$entry" ] || continue
        name="$(basename "$entry")"
        link_path="$target_parent/$name"
        if [ -e "$link_path" ] || [ -L "$link_path" ]; then
            printf '\033[33mSymlink already exists: %s\033[0m\n' "$link_path"
            continue
        fi
        echo "Creating symlink: $link_path -> $entry"
        ln -s "$entry" "$link_path"
    done
}

for entry_type in skills agents instructions; do
    add_agent_entries "$entry_type"
done
