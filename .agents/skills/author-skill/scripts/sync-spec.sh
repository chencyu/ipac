#!/bin/sh
# Sync the agentskills spec repo — clone if absent, pull if present.
# Uses $0's directory so it works regardless of shell CWD.
# Ignore all errors (offline, no git, etc.).
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$SCRIPT_DIR/../references/agentskills"
if [ -d "$REPO/.git" ]; then
    git -C "$REPO" pull --quiet 2>/dev/null
else
    git clone --quiet "https://github.com/agentskills/agentskills.git" "$REPO" 2>/dev/null
fi
exit 0
