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


$ErrorActionPreference = "Stop"

$REPO_DIR = (Get-Item -Path $PSScriptRoot).Parent.FullName
$SOURCE_DIR = Join-Path -Path $REPO_DIR -ChildPath ".agents"

$entry_specs = @(
    [pscustomobject]@{
        Source = Join-Path -Path $SOURCE_DIR -ChildPath "skills"
        Target = Join-Path -Path $HOME -ChildPath $selected_agent_profile.SkillsTargetDir
    }
    [pscustomobject]@{
        Source = Join-Path -Path $SOURCE_DIR -ChildPath "agents"
        Target = Join-Path -Path $HOME -ChildPath $selected_agent_profile.AgentsTargetDir
    }
    [pscustomobject]@{
        Source = Join-Path -Path $SOURCE_DIR -ChildPath "instructions"
        Target = Join-Path -Path $HOME -ChildPath $selected_agent_profile.InstructionsTargetDir
    }
)

function Remove-DanglingLinks {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [pscustomobject]$entry_spec
    )
    if (-not (Test-Path -Path $entry_spec.Target)) { return }

    # Other repos link into the same directory; only links into this repo are ours to remove
    $ownedPrefix = $entry_spec.Source + [IO.Path]::DirectorySeparatorChar
    $ownedLinks = Get-ChildItem -Path $entry_spec.Target -Force |
        Where-Object { $_.LinkType -eq "SymbolicLink" -and $_.LinkTarget.StartsWith($ownedPrefix, [StringComparison]::OrdinalIgnoreCase) }
    foreach ($link in $ownedLinks) {
        if (Test-Path -LiteralPath $link.LinkTarget) { continue }
        Write-Host "Removing dangling symlink: $($link.FullName) -> $($link.LinkTarget)" -ForegroundColor Yellow
        Remove-Item -LiteralPath $link.FullName
    }
}

function Add-AgentEntries {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [pscustomobject]$entry_spec
    )
    if (-not (Test-Path -Path $entry_spec.Source)) { return }

    New-Item -ItemType Directory -Path $entry_spec.Target -Force | Out-Null

    foreach ($entry in Get-ChildItem -Path $entry_spec.Source) {
        $linkPath = Join-Path -Path $entry_spec.Target -ChildPath $entry.Name
        # -Force also finds broken links, which Test-Path reports as missing
        $existing = Get-Item -LiteralPath $linkPath -Force -ErrorAction SilentlyContinue
        if ($existing) {
            if ($existing.LinkType -eq "SymbolicLink" -and $existing.Target -contains $entry.FullName) {
                Write-Host "Already linked: $linkPath" -ForegroundColor Yellow
            }
            else {
                Write-Warning "Skipped, path exists and is not a link to $($entry.FullName): $linkPath"
            }
            continue
        }
        Write-Host "Creating symlink: $linkPath -> $($entry.FullName)"
        New-Item -ItemType SymbolicLink -Path $linkPath -Target $entry.FullName | Out-Null
    }
}

foreach ($entry_spec in $entry_specs) {
    # Removing first frees names that a moved entry's new link would otherwise collide with
    Remove-DanglingLinks -entry_spec $entry_spec
    Add-AgentEntries -entry_spec $entry_spec
}
