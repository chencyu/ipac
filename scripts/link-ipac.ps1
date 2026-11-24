#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet("agent", "claude", "codex", "github", "copilot")]
    [string]$Agent = "agent",
    [Parameter()]
    [ValidateSet(".agents", ".claude", ".codex", ".github", ".copilot")]
    $AgentDirName = $null
)
class AgentProfile {
    [string]$AgentName
    [string]$SkillsTargetDir
    [string]$AgentsTargetDir
    [string]$InstructionsTargetDir
}

$general_agent = [AgentProfile] @{
    AgentName             = "agent"
    SkillsTargetDir       = Join-Path -Path ($AgentDirName ?? ".agents") -ChildPath "skills"
    AgentsTargetDir       = Join-Path -Path ($AgentDirName ?? ".agents") -ChildPath "agents"
    InstructionsTargetDir = Join-Path -Path ($AgentDirName ?? ".agents") -ChildPath "instructions"
}
$claude_agent = [AgentProfile] @{
    AgentName             = "claude"
    SkillsTargetDir       = Join-Path -Path ($AgentDirName ?? ".claude") -ChildPath "skills"
    AgentsTargetDir       = Join-Path -Path ($AgentDirName ?? ".claude") -ChildPath "agents"
    InstructionsTargetDir = Join-Path -Path ($AgentDirName ?? ".claude") -ChildPath "rules"
}
$codex_agent = [AgentProfile] @{
    AgentName             = "codex"
    SkillsTargetDir       = Join-Path -Path ($AgentDirName ?? ".agents") -ChildPath "skills"
    AgentsTargetDir       = Join-Path -Path ($AgentDirName ?? ".agents") -ChildPath "agents"
    InstructionsTargetDir = Join-Path -Path ($AgentDirName ?? ".agents") -ChildPath "instructions"
}
$github_agent = [AgentProfile] @{
    AgentName             = "github"
    SkillsTargetDir       = Join-Path -Path ($AgentDirName ?? ".github") -ChildPath "skills"
    AgentsTargetDir       = Join-Path -Path ($AgentDirName ?? ".github") -ChildPath "agents"
    InstructionsTargetDir = Join-Path -Path ($AgentDirName ?? ".github") -ChildPath "instructions"
}
$copilot_agent = [AgentProfile] @{
    AgentName             = "copilot"
    SkillsTargetDir       = Join-Path -Path ".agents" -ChildPath "skills"
    AgentsTargetDir       = Join-Path -Path ($AgentDirName ?? ".copilot") -ChildPath "agents"
    InstructionsTargetDir = Join-Path -Path ($AgentDirName ?? ".copilot") -ChildPath "instructions"
}

$selected_agent_profile = switch ($Agent) {
    "agent" { $general_agent }
    "claude" { $claude_agent }
    "codex" { $codex_agent }
    "github" { $github_agent }
    "copilot" { $copilot_agent }
}


$IPAC_DIR = $(Get-Item -Path $PSScriptRoot).Parent.FullName

function Get-AgentTargetDir {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateSet("skills", "agents", "instructions")]
        [string]$entry_type
    )

    switch ($entry_type) {
        "skills" { $selected_agent_profile.SkillsTargetDir }
        "agents" { $selected_agent_profile.AgentsTargetDir }
        "instructions" { $selected_agent_profile.InstructionsTargetDir }
    }
}

function Add-AgentEntries {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateSet("skills", "agents", "instructions")]
        [string]$entry_type
    )
    if (-not (Test-Path -Path "$IPAC_DIR/.agents/$entry_type")) { return }

    $target_dir = Get-AgentTargetDir -entry_type $entry_type
    $targetParent = Join-Path -Path $HOME -ChildPath $target_dir
    New-Item -ItemType Directory -Path $targetParent -Force -ErrorAction SilentlyContinue | Out-Null

    foreach ($entry in Get-ChildItem -Path "$IPAC_DIR/.agents/$entry_type") {
        $linkPath = Join-Path -Path $targetParent -ChildPath $entry.Name
        if (Test-Path -Path $linkPath) {
            Write-Host "Symlink already exists: $linkPath" -ForegroundColor Yellow
            continue
        }
        Write-Host "Creating symlink: $linkPath -> $entry"
        New-Item -ItemType SymbolicLink -Path $linkPath -Target $entry | Out-Null
    }
}

function Remove-DanglingLinks {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateSet("skills", "agents", "instructions")]
        [string]$entry_type
    )
    $target_dir = Get-AgentTargetDir -entry_type $entry_type
    $targetParent = Join-Path -Path $HOME -ChildPath $target_dir
    if (-not (Test-Path -Path $targetParent)) { return }

    foreach ($link in Get-ChildItem -Path $targetParent | Where-Object { $_.LinkType -and -not $_.ResolveLinkTarget($true).Exists }) {
        Write-Host "Removing dangling symlink: $($link.FullName) -> $($link.Target)" -ForegroundColor Yellow
        Remove-Item -Path $link.FullName
    }
}

foreach ($entry_type in @("skills", "agents", "instructions")) {
    Add-AgentEntries -entry_type $entry_type
}

foreach ($entry_type in @("skills", "agents", "instructions")) {
    Remove-DanglingLinks -entry_type $entry_type
}
