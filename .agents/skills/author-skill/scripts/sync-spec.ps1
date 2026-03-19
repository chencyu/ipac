# Sync the agentskills spec repo — clone if absent, pull if present.
# Uses $PSScriptRoot so it works regardless of shell CWD.
# Ignore all errors (offline, no git, etc.).
$repo = Join-Path $PSScriptRoot "..\references\agentskills"
if (Test-Path (Join-Path $repo ".git")) {
    git -C $repo pull --quiet 2>$null
}
else {
    git clone --quiet "https://github.com/agentskills/agentskills.git" $repo 2>$null
}
exit 0
