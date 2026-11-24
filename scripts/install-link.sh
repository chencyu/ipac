#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob dotglob

# Equivalent of install-link.ps1 for Linux/macOS.
# Creates symlinks for skills/agents/instructions into the selected profile target directories.

usage() {
    cat <<EOF
Usage: $(basename "$0") [-a AGENT] [-d AGENT_DIR_NAME]

Options:
  -a AGENT            Agent profile: agent | claude | codex | github | copilot (default: agent)
  -d AGENT_DIR_NAME   Override agent directory; Copilot skills remain in .agents
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

resolve_profile() {
    local default_agent_dir

    case "$AGENT" in
        agent|codex) default_agent_dir=".agents" ;;
        claude) default_agent_dir=".claude" ;;
        github) default_agent_dir=".github" ;;
        copilot) default_agent_dir=".copilot" ;;
    esac

    agent_dir_name="${AGENT_DIR_NAME:-$default_agent_dir}"
    skills_target_dir="$agent_dir_name/skills"
    agents_target_dir="$agent_dir_name/agents"
    instructions_target_dir="$agent_dir_name/instructions"

    case "$AGENT" in
        claude) instructions_target_dir="$agent_dir_name/rules" ;;
        copilot) skills_target_dir=".agents/skills" ;;
    esac
}

resolve_profile

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR="$REPO_DIR/.agents"

remove_dangling_links() {
    local source_dir="$1"
    local target_dir="$2"
    [ -d "$target_dir" ] || return 0

    local link_path link_target
    for link_path in "$target_dir"/*; do
        [ -L "$link_path" ] || continue
        link_target="$(readlink "$link_path")"
        case "$link_target" in
            "$source_dir"/*)
                if [ ! -e "$link_target" ]; then
                    printf '\033[33mRemoving dangling symlink: %s -> %s\033[0m\n' "$link_path" "$link_target"
                    rm "$link_path"
                fi
                ;;
        esac
    done
}

add_agent_entries() {
    local source_dir="$1"
    local target_dir="$2"
    [ -d "$source_dir" ] || return 0

    mkdir -p "$target_dir"

    local entry name link_path
    for entry in "$source_dir"/*; do
        name="$(basename "$entry")"
        link_path="$target_dir/$name"
        if [ -e "$link_path" ] || [ -L "$link_path" ]; then
            if [ -L "$link_path" ] && [ "$(readlink "$link_path")" = "$entry" ]; then
                printf '\033[33mAlready linked: %s\033[0m\n' "$link_path"
            else
                printf '\033[33mSkipped, path exists and is not a link to %s: %s\033[0m\n' "$entry" "$link_path" >&2
            fi
            continue
        fi
        echo "Creating symlink: $link_path -> $entry"
        ln -s "$entry" "$link_path"
    done
}

install_agent_entries() {
    local source_dir="$1"
    local target_dir="$2"

    # Removing first frees names that a moved entry's new link would otherwise collide with.
    remove_dangling_links "$source_dir" "$target_dir"
    add_agent_entries "$source_dir" "$target_dir"
}

install_agent_entries "$SOURCE_DIR/skills" "$HOME/$skills_target_dir"
install_agent_entries "$SOURCE_DIR/agents" "$HOME/$agents_target_dir"
install_agent_entries "$SOURCE_DIR/instructions" "$HOME/$instructions_target_dir"
