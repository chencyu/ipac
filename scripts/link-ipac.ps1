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
    [string]$AgentDirName
    [string]$SkillsDirName
    [string]$AgentsDirName
    [string]$InstructionsDirName
}

$general_agent = [AgentProfile] @{
    AgentName           = "agent"
    AgentDirName        = $AgentDirName ?? ".agents"
    SkillsDirName       = "skills"
    AgentsDirName       = "agents"
    InstructionsDirName = "instructions"
}
$claude_agent = [AgentProfile] @{
    AgentName           = "claude"
    AgentDirName        = $AgentDirName ?? ".claude"
    SkillsDirName       = $general_agent.SkillsDirName
    AgentsDirName       = $general_agent.AgentsDirName
    InstructionsDirName = "rules"
}
$codex_agent = [AgentProfile] @{
    AgentName           = "codex"
    AgentDirName        = $AgentDirName ?? ".agents"
    SkillsDirName       = $general_agent.SkillsDirName
    AgentsDirName       = $general_agent.AgentsDirName
    InstructionsDirName = $general_agent.InstructionsDirName
}
$github_agent = [AgentProfile] @{
    AgentName           = "github"
    AgentDirName        = $AgentDirName ?? ".github"
    SkillsDirName       = $general_agent.SkillsDirName
    AgentsDirName       = $general_agent.AgentsDirName
    InstructionsDirName = $general_agent.InstructionsDirName
}
$copilot_agent = [AgentProfile] @{
    AgentName           = "copilot"
    AgentDirName        = $AgentDirName ?? ".copilot"
    SkillsDirName       = $general_agent.SkillsDirName
    AgentsDirName       = $general_agent.AgentsDirName
    InstructionsDirName = $general_agent.InstructionsDirName
}

$selected_agent_profile = switch ($Agent) {
    "agent" { $general_agent }
    "claude" { $claude_agent }
    "codex" { $codex_agent }
    "github" { $github_agent }
    "copilot" { $copilot_agent }
}


$IPAC_DIR = $(Get-Item -Path $PSScriptRoot).Parent.FullName
$AGENT_DIR = Join-Path -Path $HOME -ChildPath $selected_agent_profile.AgentDirName

function Add-AgentEntries {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateSet("skills", "agents", "instructions")]
        [string]$entry_type
    )
    if (-not (Test-Path -Path "$IPAC_DIR/.agents/$entry_type")) { return }

    $link_entry_type = switch ($entry_type) {
        "skills" { $selected_agent_profile.SkillsDirName }
        "agents" { $selected_agent_profile.AgentsDirName }
        "instructions" { $selected_agent_profile.InstructionsDirName }
    }

    $targetParent = Join-Path -Path $AGENT_DIR -ChildPath $link_entry_type
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

foreach ($entry_type in @("skills", "agents", "instructions")) {
    Add-AgentEntries -entry_type $entry_type
}
