[CmdletBinding()]
param(
    [string]$TaskName = "MCPT EXP-003 Paper Update"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$task = Get-ScheduledTask `
    -TaskName $TaskName `
    -ErrorAction SilentlyContinue

if ($null -eq $task) {
    Write-Host (
        "EXP-003 paper task is not installed."
    )

    exit 0
}

Unregister-ScheduledTask `
    -TaskName $TaskName `
    -Confirm:$false

Write-Host ""
Write-Host "EXP-003 paper task removed."
Write-Host (
    "Existing paper data, results, reports and logs " +
    "were preserved."
)
