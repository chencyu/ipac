#!/usr/bin/env bash
set -euo pipefail

# Equivalent of link-ipac.ps1 for Linux/macOS.
# Creates symlinks for skills/agents/instructions into the selected profile target directories.

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

# Resolve agent profile target directories relative to HOME.
default_dir_name=""

case "$AGENT" in
    agent)
        default_dir_name=".agents"
        ;;
    claude)
        default_dir_name=".claude"
        ;;
    codex)
        default_dir_name=".agents"
        ;;
    github)
        default_dir_name=".github"
        ;;
    copilot)
        default_dir_name=".copilot"
        ;;
esac

agent_dir_name="${AGENT_DIR_NAME:-$default_dir_name}"
skills_target_dir="$agent_dir_name/skills"
agents_target_dir="$agent_dir_name/agents"
instructions_target_dir="$agent_dir_name/instructions"

if [ "$AGENT" = "claude" ]; then
    instructions_target_dir="$agent_dir_name/rules"
elif [ "$AGENT" = "copilot" ]; then
    skills_target_dir=".agents/skills"
fi

# Resolve directories.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IPAC_DIR="$(dirname "$SCRIPT_DIR")"

agent_target_dir() {
    local entry_type="$1"

    case "$entry_type" in
        skills) printf '%s\n' "$skills_target_dir" ;;
        agents) printf '%s\n' "$agents_target_dir" ;;
        instructions) printf '%s\n' "$instructions_target_dir" ;;
        *) echo "Unknown entry type: $entry_type" >&2; return 1 ;;
    esac
}

add_agent_entries() {
    local entry_type="$1"
    local target_dir
    target_dir="$(agent_target_dir "$entry_type")"

    local source_dir="$IPAC_DIR/.agents/$entry_type"
    if [ ! -d "$source_dir" ]; then
        return 0
    fi

    local target_parent="$HOME/$target_dir"
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

remove_dangling_links() {
    local entry_type="$1"
    local target_dir
    target_dir="$(agent_target_dir "$entry_type")"

    local target_parent="$HOME/$target_dir"
    [ -d "$target_parent" ] || return 0

    local link_path
    for link_path in "$target_parent"/*; do
        # -e follows the link, so it fails exactly when the target is gone.
        if [ -L "$link_path" ] && [ ! -e "$link_path" ]; then
            printf '\033[33mRemoving dangling symlink: %s -> %s\033[0m\n' "$link_path" "$(readlink "$link_path")"
            rm "$link_path"
        fi
    done
}

for entry_type in skills agents instructions; do
    add_agent_entries "$entry_type"
done

for entry_type in skills agents instructions; do
    remove_dangling_links "$entry_type"
done
