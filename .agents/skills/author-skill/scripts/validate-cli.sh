#!/bin/sh
# Validate a skill using the skills-ref CLI.
# Usage: ./validate-cli.sh <path-to-skill-directory>
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REF_DIR="$SCRIPT_DIR/../references/agentskills/skills-ref"
pip install -e "$REF_DIR" --quiet 2>/dev/null
skills-ref validate "$1"
