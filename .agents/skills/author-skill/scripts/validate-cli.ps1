# Validate a skill using the skills-ref CLI.
# Usage: .\validate-cli.ps1 <path-to-skill-directory>
param(
    [Parameter(Mandatory)][string]$SkillPath
)
$ref = Join-Path $PSScriptRoot "..\references\agentskills\skills-ref"
pip install -e $ref --quiet 2>$null
skills-ref validate $SkillPath
